import os
import json
from typing import List

KEYWORDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "keywords.json")


def load_keywords() -> List[List[str]]:
    """Loads keyword groups from keywords.json, with fallback to config.py."""
    if os.path.exists(KEYWORDS_FILE):
        try:
            with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[WARN] Failed to read keywords.json: {e}")

    # Fallback to config.py
    try:
        from src.config import keywords as fallback_keywords
        return [list(group) for group in fallback_keywords]
    except Exception:
        return []


def save_keywords(keywords: List[List[str]]) -> bool:
    """Saves keyword groups to keywords.json."""
    try:
        with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save keywords.json: {e}")
        return False


def add_keyword_group(group: List[str]) -> bool:
    """Adds a new keyword group and persists it."""
    clean_group = [w.strip() for w in group if w.strip()]
    if not clean_group:
        return False
    current = load_keywords()
    current.append(clean_group)
    return save_keywords(current)


def delete_keyword_group(index: int) -> bool:
    """Deletes a keyword group by index and persists changes."""
    current = load_keywords()
    if 0 <= index < len(current):
        current.pop(index)
        return save_keywords(current)
    return False
