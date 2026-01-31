"""
History Storage Module
Simple JSON file-based storage for scan history
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
import uuid
import logging

logger = logging.getLogger(__name__)

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent.parent / "data"
HISTORY_FILE = STORAGE_DIR / "history.json"


def _ensure_storage():
    """Ensure storage directory and file exist"""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, "w") as f:
            json.dump({"scans": []}, f)


def _load_history() -> Dict:
    """Load history from file"""
    _ensure_storage()
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load history: {e}")
        return {"scans": []}


def _save_history(data: Dict):
    """Save history to file"""
    _ensure_storage()
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")


def save_scan(result: Dict) -> str:
    """
    Save a scan result to history
    
    Returns:
        The generated scan ID
    """
    scan_id = str(uuid.uuid4())[:8]
    
    history = _load_history()
    
    # Create history entry
    entry = {
        "id": scan_id,
        "url": result.get("url", ""),
        "title": result.get("meta", {}).get("title", "Unknown"),
        "primary_color": result.get("colors", {}).get("primary"),
        "logo_url": result.get("logo", {}).get("url"),
        "timestamp": datetime.utcnow().isoformat(),
        "full_result": result
    }
    
    # Add to beginning of list
    history["scans"].insert(0, entry)
    
    # Keep only last 50 scans
    history["scans"] = history["scans"][:50]
    
    _save_history(history)
    
    return scan_id


def get_history() -> List[Dict]:
    """Get list of all scans (without full results)"""
    history = _load_history()
    
    # Return simplified list
    return [
        {
            "id": scan["id"],
            "url": scan["url"],
            "title": scan["title"],
            "primary_color": scan.get("primary_color"),
            "logo_url": scan.get("logo_url"),
            "timestamp": scan["timestamp"]
        }
        for scan in history.get("scans", [])
    ]


def get_scan_by_id(scan_id: str) -> Optional[Dict]:
    """Get a specific scan by ID"""
    history = _load_history()
    
    for scan in history.get("scans", []):
        if scan["id"] == scan_id:
            return scan.get("full_result")
    
    return None


def delete_scan(scan_id: str) -> bool:
    """Delete a scan by ID"""
    history = _load_history()
    
    original_length = len(history.get("scans", []))
    history["scans"] = [s for s in history.get("scans", []) if s["id"] != scan_id]
    
    if len(history["scans"]) < original_length:
        _save_history(history)
        return True
    
    return False


def clear_history() -> int:
    """Clear all history"""
    history = _load_history()
    count = len(history.get("scans", []))
    history["scans"] = []
    _save_history(history)
    return count
