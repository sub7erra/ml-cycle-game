"""
Tools package for ML Cycle Game platform.

This package provides shared utilities for:
- File I/O operations
- JSON parsing
- Text processing
- CSV processing
- Path utilities
- Streamlit utilities
- LLM utilities
"""

from .core import (
    # File I/O utilities
    read_markdown_file,
    
    # JSON parsing utilities
    extract_first_json_object,
    json_message_display_transform,
    
    # Text processing utilities
    extract_known_fields_from_text,
    
    # CSV processing utilities
    load_field_metadata_from_csv,
    
    # Path utilities
    get_download_path_for_dataset,
    get_dataset_and_fields_paths,
    
    # Streamlit utilities
    do_rerun,
    
    # LLM utilities
    get_api_key,
    get_gemini_model,
    chat_with_persona,
)

__all__ = [
    # File I/O utilities
    "read_markdown_file",
    
    # JSON parsing utilities
    "extract_first_json_object",
    "json_message_display_transform",
    
    # Text processing utilities
    "extract_known_fields_from_text",
    
    # CSV processing utilities
    "load_field_metadata_from_csv",
    
    # Path utilities
    "get_download_path_for_dataset",
    "get_dataset_and_fields_paths",
    
    # Streamlit utilities
    "do_rerun",
    
    # LLM utilities
    "get_api_key",
    "get_gemini_model",
    "chat_with_persona",
]
