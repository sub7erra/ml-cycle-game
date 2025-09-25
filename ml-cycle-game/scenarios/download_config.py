"""
Download configuration system for ML Cycle Game scenarios.

This module provides dataclasses to declaratively configure available downloads
for each scenario, organized by room and file type.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class FileType(Enum):
    """Types of files available for download."""
    DATASET = "dataset"
    FIELDS = "fields"
    DOCUMENTATION = "documentation"
    REFERENCE = "reference"


class DownloadGroup(Enum):
    """Groups for organizing downloads."""
    DATA = "data"
    METADATA = "metadata"
    DOCS = "docs"


@dataclass
class DownloadFile:
    """Configuration for a single downloadable file."""
    filename: str
    file_type: FileType
    group: DownloadGroup
    description: str
    
    def get_path(self, scenario_dir: Path) -> Path:
        """Get the full path to this file."""
        return scenario_dir / "data" / self.filename
    
    def exists(self, scenario_dir: Path) -> bool:
        """Check if this file exists."""
        return self.get_path(scenario_dir).exists()
    
    def validate(self, scenario_dir: Path) -> None:
        """Validate that the file exists."""
        if not self.exists(scenario_dir):
            raise FileNotFoundError(
                f"Required file '{self.filename}' not found in {scenario_dir / 'data'}"
            )


@dataclass
class RoomDownloads:
    """Download configuration for a specific room."""
    room_number: int
    room_name: str
    files: List[DownloadFile] = field(default_factory=list)
    
    def get_files_by_type(self, file_type: FileType) -> List[DownloadFile]:
        """Get all files of a specific type in this room."""
        return [f for f in self.files if f.file_type == file_type]
    
    def get_files_by_group(self, group: DownloadGroup) -> List[DownloadFile]:
        """Get all files in a specific group in this room."""
        return [f for f in self.files if f.group == group]
    
    def validate_all(self, scenario_dir: Path) -> None:
        """Validate all files in this room."""
        for file_config in self.files:
            file_config.validate(scenario_dir)


class BaseDownloadConfig(ABC):
    """Base class for scenario download configurations."""
    
    def __init__(self, scenario_dir: Path):
        self.scenario_dir = scenario_dir
        self.rooms = self._get_room_configs()
        self._validate_all()
    
    @abstractmethod
    def _get_room_configs(self) -> Dict[int, RoomDownloads]:
        """Get the room download configurations. Must be implemented by subclasses."""
        pass
    
    def _validate_all(self) -> None:
        """Validate all download configurations."""
        for room in self.rooms.values():
            room.validate_all(self.scenario_dir)
    
    def get_room_downloads(self, room_number: int) -> Optional[RoomDownloads]:
        """Get download configuration for a specific room."""
        return self.rooms.get(room_number)
    
    def get_all_files_by_type(self, file_type: FileType) -> List[DownloadFile]:
        """Get all files of a specific type across all rooms."""
        files = []
        for room in self.rooms.values():
            files.extend(room.get_files_by_type(file_type))
        return files
    
    def get_all_files_by_group(self, group: DownloadGroup) -> List[DownloadFile]:
        """Get all files in a specific group across all rooms."""
        files = []
        for room in self.rooms.values():
            files.extend(room.get_files_by_group(group))
        return files
