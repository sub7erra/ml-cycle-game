"""
Base scenario class for ML Cycle Game platform.

This module provides the base Scenario class that all specific scenarios should inherit from.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import streamlit as st

from tools import read_markdown_file, load_field_metadata_from_csv
from .download_config import BaseDownloadConfig


class BaseScenario(ABC):
    """Base class for all scenarios in the ML Cycle Game platform."""
    
    @classmethod
    @abstractmethod
    def get_label(cls) -> str:
        """Return a short, human-readable label for this scenario."""
        pass
    
    def __init__(self, scenario_dir: Path):
        """Initialize the scenario with its directory path."""
        self.scenario_dir = scenario_dir
        self.rooms_dir = scenario_dir / "rooms"
        self.lore_path = scenario_dir / "lore.md"
        self.lore_text = read_markdown_file(self.lore_path)
        
        # Load field metadata if available
        fields_csv = scenario_dir / "data" / "fields.csv"
        if fields_csv.exists():
            if "field_metadata" not in st.session_state:
                st.session_state.field_metadata = load_field_metadata_from_csv(fields_csv)
        
        # Initialize download configuration
        self.download_config = self._get_download_config()
    
    @abstractmethod
    def _get_download_config(self) -> BaseDownloadConfig:
        """Get the download configuration for this scenario. Must be implemented by subclasses."""
        pass
    
    def render_scenario(self):
        """Main entry point for rendering the scenario."""
        st.title("Escape Room: Data Science Lifecycle")
        st.caption("An interactive, scenario-based learning experience")

        if "room_index" not in st.session_state:
            st.session_state.room_index = 0
        if "max_room_unlocked" not in st.session_state:
            st.session_state.max_room_unlocked = 0

        # Clamp current room to highest unlocked
        st.session_state.room_index = min(st.session_state.room_index, st.session_state.max_room_unlocked)
        room = st.session_state.room_index

        # Route to appropriate room handler
        self._render_room(room)
    
    @abstractmethod
    def _render_room(self, room: int):
        """Render the specified room. Must be implemented by subclasses."""
        pass
    
    def render_room_markdown(self, md_path: Path):
        """Helper method to render markdown files."""
        content = read_markdown_file(md_path)
        st.markdown(content)
    
    def render_downloads_for_room(self, room_number: int):
        """Render download buttons for files available in the specified room."""
        room_downloads = self.download_config.get_room_downloads(room_number)
        if not room_downloads or not room_downloads.files:
            return
        
        # Check if room downloads are unlocked
        if not self._is_room_downloads_unlocked(room_number):
            return
        
        # Render download buttons
        st.subheader("Available Downloads")
        
        # Display files with descriptions
        for file_config in room_downloads.files:
            file_path = file_config.get_path(self.scenario_dir)
            if file_path.exists():
                # Show file info with description
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{file_config.filename}**")
                    st.caption(file_config.description)
                with col2:
                    st.download_button(
                        label="Download",
                        data=file_path.read_bytes(),
                        file_name=file_config.filename,
                        mime="text/csv" if file_config.filename.endswith('.csv') else "application/octet-stream",
                        help=f"Download {file_config.filename}",
                        key=f"download_{file_config.filename}_{room_number}",
                    )
    
    def _is_room_downloads_unlocked(self, room_number: int) -> bool:
        """Check if downloads for a specific room are unlocked. Override in subclasses for custom logic."""
        # Default implementation - can be overridden by subclasses
        return True
