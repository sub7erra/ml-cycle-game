import random
from typing import List

import streamlit as st
import pandas as pd  # type: ignore

from scenarios import BaseScenario
from .download_config import HousePricePredictionDownloadConfig
from tools import (
    read_markdown_file,
    json_message_display_transform,
    extract_first_json_object,
    extract_known_fields_from_text,
    do_rerun,
)
from app import ui_chat_area


class HousePricePredictionScenario(BaseScenario):
    """Scenario implementation for house price prediction escape room."""
    
    @classmethod
    def get_label(cls) -> str:
        """Return a short, human-readable label for this scenario."""
        return "House Price Prediction"
    
    def _get_download_config(self):
        """Get the download configuration for this scenario."""
        return HousePricePredictionDownloadConfig(self.scenario_dir)
    
    def _is_room_downloads_unlocked(self, room_number: int) -> bool:
        """Check if downloads for a specific room are unlocked."""
        if room_number == 3:  # EDA room
            # Downloads are unlocked when at least 10 fields are discovered
            return (len(st.session_state.get("discovered_fields", [])) >= 10 or 
                    len(st.session_state.get("discovered_fields_info", {})) >= 10)
        return True  # Other rooms have no unlock conditions
    
    def _render_room(self, room: int):
        """Render the specified room."""
        if room == 0:
            self.render_room_0_introduction()
        elif room == 1:
            self.render_room_1_briefing()
        elif room == 2:
            self.render_room_2_discovery()
        elif room == 3:
            self.render_room_3_eda()
        elif room == 4:
            self.render_room_4_engineering()
        elif room == 5:
            self.render_room_5_submission()
    
    def render_room_0_introduction(self):
        """Render the introduction room."""
        self.render_room_markdown(self.rooms_dir / "room_0_introduction.md")
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("Return to start", disabled=True)
        with col_next:
            if st.button("Go to Room 1: Briefing"):
                st.session_state.room_index = 1
                st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 1)
                do_rerun()
    
    def render_room_1_briefing(self):
        """Render the briefing room."""
        self.render_room_markdown(self.rooms_dir / "room_1_briefing.md")
        system_prompt = read_markdown_file(self.rooms_dir / "room_1_briefing_system.md") + "\n\n" + self.lore_text
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
    
    def render_room_2_discovery(self):
        """Render the data discovery room."""
        self.render_room_markdown(self.rooms_dir / "room_2_discovery.md")
        system_prompt = read_markdown_file(self.rooms_dir / "room_2_discovery_system.md") + "\n\n" + self.lore_text
        
        # Initialize discovered fields tracking
        if "discovered_fields_info" not in st.session_state:
            st.session_state.discovered_fields_info = {}
        
        # Back-compat: migrate any old set to dict with descriptions
        if "discovered_fields" in st.session_state and isinstance(st.session_state.discovered_fields, set):
            for fname in list(st.session_state.discovered_fields):
                if fname not in st.session_state.discovered_fields_info:
                    desc = st.session_state.field_metadata.get(fname, {}).get("description")
                    st.session_state.discovered_fields_info[fname] = desc

        # Lightweight instruction for users
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
    
    def render_room_3_eda(self):
        """Render the EDA room."""
        self.render_room_markdown(self.rooms_dir / "room_3_eda.md")
        
        # Render downloads using the configuration system
        self.render_downloads_for_room(3)
        
        # Show warning if downloads are not yet unlocked
        if not self._is_room_downloads_unlocked(3):
            st.warning("Discover at least 10 fields in Room 2 to unlock the dataset download.")

        system_prompt = read_markdown_file(self.rooms_dir / "room_3_eda_system.md") + "\n\n" + self.lore_text
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
    
    def render_room_4_engineering(self):
        """Render the feature engineering room."""
        self.render_room_markdown(self.rooms_dir / "room_4_engineering.md")
        system_prompt = read_markdown_file(self.rooms_dir / "room_4_engineering_system.md") + "\n\n" + self.lore_text

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
    
    def render_room_5_submission(self):
        """Render the final submission room."""
        self.render_room_markdown(self.rooms_dir / "room_5_submission.md")
        
        # Get dataset path from download configuration
        room_downloads = self.download_config.get_room_downloads(3)  # Dataset is in room 3
        dataset_file = None
        if room_downloads:
            for file_config in room_downloads.files:
                if file_config.file_type.value == "dataset":
                    dataset_file = file_config
                    break
        
        if dataset_file and dataset_file.get_path(self.scenario_dir).exists():
            try:
                dataset_path = dataset_file.get_path(self.scenario_dir)
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
    
