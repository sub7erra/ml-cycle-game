import os
import json
import re
import threading
import queue
import random
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Tuple

import streamlit as st  # type: ignore
import pandas as pd  # type: ignore

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


def list_scenarios() -> List[str]:
    if not SCENARIOS_DIR.exists():
        return []
    return [p.name for p in SCENARIOS_DIR.iterdir() if p.is_dir()]


def read_markdown_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def get_api_key() -> Optional[str]:
    # Priority: Streamlit secrets → .env → env var
    key = None
    try:
        key = st.secrets.get("GOOGLE_API_KEY")  # type: ignore
    except Exception:
        key = None
    if not key:
        key = os.getenv("GOOGLE_API_KEY")
    return key


# -----------------------------
# JSON extraction helpers
# -----------------------------

def extract_first_json_object(text: str) -> Optional[dict]:
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Strip common code fences
    fenced = text.strip()
    if fenced.startswith("```"):
        # remove first and last fence
        fenced = re.sub(r"^```[a-zA-Z]*\n", "", fenced)
        fenced = re.sub(r"\n```\s*$", "", fenced)
        try:
            return json.loads(fenced)
        except Exception:
            pass
    # Find first JSON object substring
    candidates = re.findall(r"\{[\s\S]*?\}", text)
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:
            continue
    return None


def extract_known_fields_from_text(text: str, known_fields: List[str]) -> List[str]:
    found: List[str] = []
    lower_text = text.lower()
    for name in known_fields:
        pattern = re.compile(r"\b" + re.escape(name.lower()) + r"\b")
        if pattern.search(lower_text):
            found.append(name)
    return found


def json_message_display_transform(reply: str) -> str:
    """Extract the 'message' field from JSON responses for clean display."""
    data = extract_first_json_object(reply)
    if isinstance(data, dict):
        msg = data.get("message")
        if isinstance(msg, str) and msg:
            return msg
    return reply


# -----------------------------
# Lore parsing helpers
# -----------------------------
def load_field_metadata_from_csv(csv_path: Path) -> Dict[str, Dict[str, str]]:
    import csv
    field_to_meta: Dict[str, Dict[str, str]] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            field_to_meta[name] = {
                "description": (row.get("description") or "").strip(),
                "type": (row.get("type") or "").strip(),
                "category": (row.get("category") or "").strip(),
                "is_target": (row.get("is_target") or "false").strip().lower(),
            }
    return field_to_meta


# -----------------------------
# LLM utilities (Gemini via google-generativeai)
# -----------------------------
def get_gemini_model(system_instruction: str):
    import google.generativeai as genai  # type: ignore

    api_key = get_api_key()
    if not api_key:
        st.warning("GOOGLE_API_KEY is not set. Add it to .env for local or secrets for cloud.")
        return None
    genai.configure(api_key=api_key)  # type: ignore
    # Use configured model; change via GEMINI_MODEL_NAME env var
    return genai.GenerativeModel(  # type: ignore
        model_name=GEMINI_MODEL_NAME,
        system_instruction=system_instruction,
    )


def chat_with_persona(system_prompt: str, user_content: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    model = get_gemini_model(system_prompt)
    if model is None:
        return "[LLM unavailable: missing API key]"

    # Convert our stored messages to Gemini history format
    def to_gemini_history(msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        gem_hist: List[Dict[str, Any]] = []
        for m in msgs:
            role = m.get("role")
            if role not in ("user", "assistant"):
                continue
            content = m.get("original", m.get("content", ""))
            if not isinstance(content, str) or not content:
                continue
            gem_role = "user" if role == "user" else "model"
            gem_hist.append({"role": gem_role, "parts": [content]})
        return gem_hist

    gem_history = to_gemini_history(history or [])

    result_q: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=1)

    def _worker() -> None:
        try:
            chat = model.start_chat(history=gem_history)  # type: ignore
            response = chat.send_message(user_content)  # type: ignore
            text = (getattr(response, "text", None) or "") if response else ""
            result_q.put(text)
        except Exception as exc:  # ensure thread never raises
            result_q.put(f"[LLM error: {exc}]")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    try:
        text = result_q.get(timeout=LLM_TIMEOUT_SECS)
        return text or ""
    except queue.Empty:
        return "[LLM timeout: please try again or simplify your message]"


# -----------------------------
# Streamlit helpers
# -----------------------------
def do_rerun() -> None:
    try:
        # Modern Streamlit
        st.rerun()  # type: ignore[attr-defined]
    except Exception:
        # Back-compat for older versions
        try:
            getattr(st, "experimental_rerun")()
        except Exception:
            pass


# -----------------------------
# Scenario rendering
# -----------------------------
def scenario_selector() -> Optional[str]:
    st.sidebar.header("Scenario")
    scenarios = list_scenarios()
    if not scenarios:
        st.error("No scenarios found in 'scenarios/'. Please add one and reload.")
        return None
    selected = st.sidebar.selectbox("Choose a scenario", scenarios, index=0)
    return selected


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
        user_input = st.chat_input("Your message")
    else:
        st.caption("This room is unlocked. Chat is disabled. Use navigation to proceed.")

    if user_input:
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


def get_download_path_for_dataset(scenario_name: str) -> Optional[Path]:
    data_dir = PROJECT_ROOT / "scenarios" / scenario_name / "data"
    if not data_dir.exists():
        return None
    # Prefer CSVs that are not the fields catalog
    preferred: Optional[Path] = None
    for p in sorted(data_dir.glob("*.csv")):
        if p.name.lower() == "fields.csv":
            continue
        preferred = p
        break
    return preferred


def get_dataset_and_fields_paths(scenario_name: str) -> Tuple[Optional[Path], Optional[Path]]:
    data_dir = PROJECT_ROOT / "scenarios" / scenario_name / "data"
    if not data_dir.exists():
        return None, None
    dataset: Optional[Path] = None
    fields: Optional[Path] = None
    for p in sorted(data_dir.glob("*.csv")):
        if p.name.lower() == "fields.csv":
            fields = p
        else:
            # first non-fields CSV is the dataset
            if dataset is None:
                dataset = p
    return dataset, fields


def render_scenario(scenario_name: str):
    st.title("Escape Room: Data Science Lifecycle")
    st.caption("An interactive, scenario-based learning experience")

    scenario_dir = SCENARIOS_DIR / scenario_name
    rooms_dir = scenario_dir / "rooms"
    lore_path = scenario_dir / "lore.md"

    if "room_index" not in st.session_state:
        st.session_state.room_index = 0
    if "max_room_unlocked" not in st.session_state:
        st.session_state.max_room_unlocked = 0

    # Clamp current room to highest unlocked
    st.session_state.room_index = min(st.session_state.room_index, st.session_state.max_room_unlocked)
    room = st.session_state.room_index

    # Shared lore text used in prompts
    lore_text = read_markdown_file(lore_path)
    # Always load field metadata from fields.csv (canonical)
    fields_csv = scenario_dir / "data" / "fields.csv"
    if "field_metadata" not in st.session_state:
        st.session_state.field_metadata = load_field_metadata_from_csv(fields_csv)

    if room == 0:
        render_room_markdown(rooms_dir / "room_0_introduction.md")
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("Return to start", disabled=True)
        with col_next:
            if st.button("Go to Room 1: Briefing"):
                st.session_state.room_index = 1
                st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 1)
                do_rerun()

    elif room == 1:
        render_room_markdown(rooms_dir / "room_1_briefing.md")
        system_prompt = read_markdown_file(rooms_dir / "room_1_briefing_system.md") + "\n\n" + lore_text
        unlocked = ui_chat_area(
            "briefing",
            system_prompt,
            unlock_field="unlocked",
            assistant_display_transform=json_message_display_transform,
            disable_on_unlock=True,
        )
        if unlocked:
            st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 2)
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("Return to Room 0: Introduction"):
                st.session_state.room_index = 0
                do_rerun()
        with col_next:
            st.button(
                "Go to Room 2: Data Discovery",
                disabled=st.session_state.max_room_unlocked < 2,
                on_click=lambda: (st.session_state.__setitem__("room_index", 2)),
            )

    elif room == 2:
        render_room_markdown(rooms_dir / "room_2_discovery.md")
        system_prompt = read_markdown_file(rooms_dir / "room_2_discovery_system.md") + "\n\n" + lore_text
        # Unlock when at least 10 confirmed fields are gathered
        if "discovered_fields_info" not in st.session_state:
            st.session_state.discovered_fields_info = {}
        # Back-compat: migrate any old set to dict with descriptions
        if "discovered_fields" in st.session_state and isinstance(st.session_state.discovered_fields, set):
            for fname in list(st.session_state.discovered_fields):
                if fname not in st.session_state.discovered_fields_info:
                    desc = st.session_state.field_metadata.get(fname, {}).get("description")
                    st.session_state.discovered_fields_info[fname] = desc

        # lightweight instruction for users
        st.info("Ask questions about available data fields. When a field is confirmed, it will be added below. Collect at least 10.")

        # Handle chat and parse confirmations via callback
        def on_ds_message(reply: str) -> None:
            # Steward must respond with a JSON object {message, status, confirmed_fields}
            try:
                data = extract_first_json_object(reply) or {}
            except Exception:
                return
            status = str(data.get("status", "")).lower()
            confirmed_fields = data.get("confirmed_fields") if isinstance(data, dict) else None
            added_any = False
            if status == "confirmed" and isinstance(confirmed_fields, list):
                for fn in confirmed_fields:
                    if isinstance(fn, str) and fn:
                        desc = st.session_state.field_metadata.get(fn, {}).get("description")
                        st.session_state.discovered_fields_info[fn] = desc
                        added_any = True
            # Fallback: if model omitted confirmed_fields, try to detect known field names in the message text
            if not added_any:
                msg = data.get("message") if isinstance(data, dict) else None
                if isinstance(msg, str) and msg:
                    known = list(st.session_state.field_metadata.keys())
                    matched = extract_known_fields_from_text(msg, known)
                    for fn in matched:
                        desc = st.session_state.field_metadata.get(fn, {}).get("description")
                        st.session_state.discovered_fields_info[fn] = desc
            # Do not re-append assistant message; UI transform handles presentation

        ui_chat_area(
            "discovery",
            system_prompt,
            "__not_used__",
            on_assistant_message=on_ds_message,
            assistant_display_transform=json_message_display_transform,
            disable_on_unlock=True,
        )

        st.subheader("Discovered fields")
        discovered_items = sorted(list(st.session_state.discovered_fields_info.items()))
        if discovered_items:
            lines = []
            for name, desc in discovered_items:
                if desc:
                    lines.append(f"- `{name}` — {desc}")
                else:
                    lines.append(f"- `{name}`")
            st.markdown("\n".join(lines))
        else:
            st.caption("No fields discovered yet.")
        discovered_enough_fields = len(st.session_state.discovered_fields_info) >= 10
        if discovered_enough_fields:
            st.success("Great! You discovered enough fields. Proceed to Room 3.")
            st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 3)
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("Return to Room 1: Briefing"):
                st.session_state.room_index = 1
                do_rerun()
        with col_next:
            st.button(
                "Go to Room 3: EDA Report",
                disabled=st.session_state.max_room_unlocked < 3,
                on_click=lambda: (st.session_state.__setitem__("room_index", 3)),
            )

    elif room == 3:
        render_room_markdown(rooms_dir / "room_3_eda.md")
        # Provide dataset download link once Room 2 completed condition met
        dataset_path, fields_path = get_dataset_and_fields_paths(scenario_name)
        unlocked_download = (len(st.session_state.get("discovered_fields", [])) >= 10 or len(st.session_state.get("discovered_fields_info", {})) >= 10)
        if unlocked_download and (dataset_path or fields_path):
            cols = st.columns(2)
            if dataset_path:
                with cols[0]:
                    st.download_button(
                        label=f"Download {dataset_path.name}",
                        data=dataset_path.read_bytes(),
                        file_name=dataset_path.name,
                        mime="text/csv",
                    )
            if fields_path:
                with cols[1]:
                    st.download_button(
                        label="Download fields.csv",
                        data=fields_path.read_bytes(),
                        file_name=fields_path.name,
                        mime="text/csv",
                    )
        else:
            st.warning("Discover at least 10 fields in Room 2 to unlock the dataset download.")

        system_prompt = read_markdown_file(rooms_dir / "room_3_eda_system.md") + "\n\n" + lore_text
        unlocked = ui_chat_area(
            "eda",
            system_prompt,
            unlock_field="unlocked",
            assistant_display_transform=json_message_display_transform,
            disable_on_unlock=True,
        )
        if unlocked:
            st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 4)
        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("Return to Room 2: Data Discovery"):
                st.session_state.room_index = 2
                do_rerun()
        with col_next:
            st.button(
                "Go to Room 4: Feature Engineering",
                disabled=st.session_state.max_room_unlocked < 4,
                on_click=lambda: (st.session_state.__setitem__("room_index", 4)),
            )

    elif room == 4:
        render_room_markdown(rooms_dir / "room_4_engineering.md")
        system_prompt = read_markdown_file(rooms_dir / "room_4_engineering_system.md") + "\n\n" + lore_text

        if "feature_points" not in st.session_state:
            st.session_state.feature_points = 0
        if "engineering_processed_count" not in st.session_state:
            st.session_state.engineering_processed_count = 0

        # Run chat; we will parse assistant JSON
        ui_chat_area(
            "engineering",
            system_prompt,
            "__not_used__",
            assistant_display_transform=json_message_display_transform,
            disable_on_unlock=True,
        )
        messages = st.session_state.get("messages_engineering", [])

        # Process only new assistant messages since last visit
        start_idx = int(st.session_state.engineering_processed_count)
        if start_idx < len(messages):
            new_msgs = messages[start_idx:]
            points_added = 0
            for msg in new_msgs:
                if msg.get("role") != "assistant":
                    continue
                original = msg.get("original", msg.get("content", ""))
                data = extract_first_json_object(original)
                if isinstance(data, dict) and "points_awarded" in data:
                    try:
                        points_added += int(data.get("points_awarded", 0))
                    except Exception:
                        pass
            if points_added:
                st.session_state.feature_points += points_added
                st.info(f"Points this turn: {points_added}")
            st.session_state.engineering_processed_count = len(messages)

        st.metric("Total points", st.session_state.feature_points)
        if st.session_state.feature_points >= 30:
            st.success("You reached 30 points! Proceed to Room 5.")
            st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 5)

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("Return to Room 3: EDA Report"):
                st.session_state.room_index = 3
                do_rerun()
        with col_next:
            st.button(
                "Go to Room 5: Submission",
                disabled=st.session_state.max_room_unlocked < 5,
                on_click=lambda: (st.session_state.__setitem__("room_index", 5)),
            )

    elif room == 5:
        render_room_markdown(rooms_dir / "room_5_submission.md")
        # Build a column selector using dataset header if available
        dataset_path = get_download_path_for_dataset(scenario_name)
        if dataset_path and dataset_path.exists():
            try:
                df_head = pd.read_csv(dataset_path, nrows=200)
                columns = list(df_head.columns)
                # Shuffle options once per session for Room 5
                if (
                    "room5_columns_order" not in st.session_state
                    or st.session_state.get("room5_columns_source") != columns
                ):
                    shuffled = columns[:]
                    random.shuffle(shuffled)
                    st.session_state.room5_columns_order = shuffled
                    st.session_state.room5_columns_source = columns
                options = st.session_state.room5_columns_order
                # Preselect all; students must deselect redundancies
                default_selection = options
                selected: List[str] = st.multiselect(
                    "Select features to hand off to modeling",
                    options=options,
                    default=default_selection,
                )
                if st.button("Submit"):
                    # Generic validation without revealing exact fields
                    if "id" in selected or "date" in selected:
                        st.error("There are still some redundant columns. Please review and deselect them.")
                    else:
                        st.success("You escaped! Great job.")
                        st.balloons()
            except Exception as exc:
                st.warning(f"Could not read dataset for columns: {exc}")
        else:
            st.info("Dataset not available yet. Add a CSV to the scenario data folder.")

        col_prev, _ = st.columns(2)
        with col_prev:
            if st.button("Return to Room 4: Feature Engineering"):
                st.session_state.room_index = 4
                do_rerun()


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


