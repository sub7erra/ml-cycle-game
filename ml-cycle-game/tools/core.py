"""
Tools module containing shared utilities for the ML Cycle Game platform.

This module contains:
- File I/O utilities
- JSON parsing utilities
- Text processing utilities
- CSV processing utilities
- Path utilities
- Streamlit utilities
- LLM utilities
"""

import os
import json
import re
import threading
import queue
import csv
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

import streamlit as st  # type: ignore

# Optional: load .env locally; on cloud, use secrets
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


# -----------------------------
# Constants
# -----------------------------
LLM_TIMEOUT_SECS = int(os.getenv("LLM_TIMEOUT_SECS", "15"))
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")
MAX_USER_MSG_CHARS = int(os.getenv("MAX_USER_MSG_CHARS", "1000"))


# -----------------------------
# File I/O utilities
# -----------------------------

def read_markdown_file(path: Path) -> str:
    """Read a markdown file and return its contents."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# -----------------------------
# JSON parsing utilities
# -----------------------------

def extract_first_json_object(text: str) -> Optional[dict]:
    """Extract the first JSON object from text, handling various formats."""
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


def json_message_display_transform(reply: str) -> str:
    """Extract the 'message' field from JSON responses for clean display."""
    data = extract_first_json_object(reply)
    if isinstance(data, dict):
        msg = data.get("message")
        if isinstance(msg, str) and msg:
            return msg
    return reply


# -----------------------------
# Text processing utilities
# -----------------------------

def extract_known_fields_from_text(text: str, known_fields: List[str]) -> List[str]:
    """Extract known field names from text using regex matching."""
    found: List[str] = []
    lower_text = text.lower()
    for name in known_fields:
        pattern = re.compile(r"\b" + re.escape(name.lower()) + r"\b")
        if pattern.search(lower_text):
            found.append(name)
    return found


# -----------------------------
# CSV processing utilities
# -----------------------------

def load_field_metadata_from_csv(csv_path: Path) -> Dict[str, Dict[str, str]]:
    """Load field metadata from a CSV file."""
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
# Path utilities
# -----------------------------

def get_download_path_for_dataset(scenario_name: str, project_root: Path) -> Optional[Path]:
    """Get the path to the main dataset file for download."""
    data_dir = project_root / "scenarios" / scenario_name / "data"
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


def get_dataset_and_fields_paths(scenario_name: str, project_root: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """Get paths to both dataset and fields CSV files."""
    data_dir = project_root / "scenarios" / scenario_name / "data"
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


# -----------------------------
# Streamlit utilities
# -----------------------------

def do_rerun() -> None:
    """Trigger a Streamlit rerun, handling version compatibility."""
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
# LLM utilities
# -----------------------------

def get_api_key() -> Optional[str]:
    """Get the Google API key from various sources."""
    # Priority: Streamlit secrets → .env → env var
    key = None
    try:
        key = st.secrets.get("GOOGLE_API_KEY")  # type: ignore
    except Exception:
        key = None
    if not key:
        key = os.getenv("GOOGLE_API_KEY")
    return key


def get_gemini_model(system_instruction: str):
    """Get a configured Gemini model instance."""
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


def chat_with_persona(system_prompt: str, user_content: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Chat with a persona using the Gemini model."""
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
        text = result_q.get(timeout=int(LLM_TIMEOUT_SECS))
        return text or ""
    except queue.Empty:
        return "[LLM timeout: please try again or simplify your message]"
