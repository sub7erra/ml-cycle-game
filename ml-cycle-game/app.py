import os
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple

import streamlit as st  # type: ignore

# Import utilities from tools package
from tools import (
    read_markdown_file,
    extract_first_json_object,
    get_download_path_for_dataset as _get_download_path,
    get_dataset_and_fields_paths as _get_dataset_and_fields_paths,
    chat_with_persona,
)

# Optional: load .env locally; on cloud, use secrets
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


# -----------------------------
# Constants and helpers
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
LLM_TIMEOUT_SECS = int(os.getenv("LLM_TIMEOUT_SECS", "15"))
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")
MAX_USER_MSG_CHARS = int(os.getenv("MAX_USER_MSG_CHARS", "1000"))


def get_download_path_for_dataset(scenario_name: str) -> Optional[Path]:
    """Get the path to the main dataset file for download."""
    return _get_download_path(scenario_name, PROJECT_ROOT)


def get_dataset_and_fields_paths(scenario_name: str) -> Tuple[Optional[Path], Optional[Path]]:
    """Get paths to both dataset and fields CSV files."""
    return _get_dataset_and_fields_paths(scenario_name, PROJECT_ROOT)


# -----------------------------
# Scenario rendering
# -----------------------------
def scenario_selector():
    st.sidebar.header("Scenario")
    from scenarios import list_scenarios
    scenario_classes = list_scenarios()
    if not scenario_classes:
        st.error("No scenarios found. Please add one and reload.")
        return None
    
    # Create display options with labels
    options = []
    for scenario_class in scenario_classes:
        label = scenario_class.get_label()
        options.append((scenario_class, label))
    
    selected_option = st.sidebar.selectbox("Choose a scenario", options, format_func=lambda x: x[1], index=0)
    return selected_option[0] if selected_option else None


def render_room_markdown(md_path: Path):
    content = read_markdown_file(md_path)
    st.markdown(content)


def ui_chat_area(
    key_prefix: str,
    system_prompt: str,
    unlock_phrase: str = "[UNLOCK]",
    on_assistant_message: Optional[Callable[[str], None]] = None,
    assistant_display_transform: Optional[Callable[[str], str]] = None,
    unlock_field: Optional[str] = None,
    disable_input: Optional[bool] = None,
    disable_on_unlock: bool = False,
) -> bool:
    if f"messages_{key_prefix}" not in st.session_state:
        st.session_state[f"messages_{key_prefix}"] = []  # list of dicts {role, content}

    messages: List[Dict[str, str]] = st.session_state[f"messages_{key_prefix}"]

    # Normalize stored assistant messages so history shows only human-friendly text
    if assistant_display_transform is not None:
        updated_messages: List[Dict[str, str]] = []
        for m in messages:
            if isinstance(m, dict) and m.get("role") == "assistant" and "original" not in m:
                original_content = m.get("content", "")
                data = extract_first_json_object(original_content)
                if isinstance(data, dict):
                    m["original"] = original_content
                    try:
                        m["content"] = assistant_display_transform(original_content)
                    except Exception:
                        pass
            updated_messages.append(m)
        st.session_state[f"messages_{key_prefix}"] = updated_messages
        messages = updated_messages

    # Pre-check unlock status based on existing history
    def history_unlocked() -> bool:
        if unlock_field:
            for msg in messages:
                if msg.get("role") == "assistant":
                    original_content = msg.get("original", msg.get("content", ""))
                    data = extract_first_json_object(original_content)
                    if isinstance(data, dict) and data.get(unlock_field) is True:
                        return True
            return False
        else:
            return any(unlock_phrase in m.get("content", "") for m in messages if m.get("role") == "assistant")

    unlocked_from_history = history_unlocked()

    # Show history
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg.get("content", ""))

    # Determine if input should be disabled
    input_disabled = bool(disable_input) or (disable_on_unlock and unlocked_from_history)

    user_input = None
    if not input_disabled:
        st.caption(f"Max message length: {MAX_USER_MSG_CHARS} characters.")
        user_input = st.chat_input("Your message")
    else:
        st.caption("This room is unlocked. Chat is disabled. Use navigation to proceed.")

    if user_input:
        if len(user_input) > MAX_USER_MSG_CHARS:
            with st.chat_message("assistant"):
                st.error(f"Your message is too long (>{MAX_USER_MSG_CHARS} chars). Please shorten and resend.")
        else:
            messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Pass prior history messages (excluding the just-added user input)
                    prior_history = messages[:-1]
                    reply = chat_with_persona(system_prompt, user_input, history=prior_history)
                display_reply = assistant_display_transform(reply) if assistant_display_transform else reply
                st.markdown(display_reply)
            # Store both original and display versions for unlock detection
            messages.append({"role": "assistant", "content": display_reply, "original": reply})
            if on_assistant_message is not None:
                try:
                    on_assistant_message(reply)
                except Exception:
                    pass

    # Determine unlock (including any new messages just added)
    unlocked = history_unlocked()

    if unlocked:
        st.success("Door unlocked! Proceed to the next room.")
    return unlocked


def render_scenario(scenario_class):
    """Generic scenario renderer that loads the appropriate scenario class."""
    try:
        # Map class name to directory name
        class_name = scenario_class.__name__
        if class_name == "HousePricePredictionScenario":
            scenario_name = "house_price_prediction"
        else:
            # Default mapping: remove 'Scenario' suffix and convert to snake_case
            scenario_name = class_name.replace('Scenario', '').lower()
        
        scenario_dir = SCENARIOS_DIR / scenario_name
        scenario = scenario_class(scenario_dir)
        scenario.render_scenario()
    except Exception as e:
        st.error(f"Error rendering scenario: {e}")


def main():
    st.set_page_config(page_title="Escape Room Platform", page_icon="🗝️", layout="wide")
    st.sidebar.title("Escape Room Platform")
    st.sidebar.caption("Modular, scenario-based learning")

    scenario = scenario_selector()
    if not scenario:
        return
    render_scenario(scenario)


if __name__ == "__main__":
    main()


