"""Utility helpers for persisting extracted variables without PyYAML."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

EXTRACT_FILE = Path("extract.yaml")


def _load_extract() -> Dict[str, Any]:
    if not EXTRACT_FILE.exists():
        return {}
    text = EXTRACT_FILE.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def write_extract(data: Dict[str, Any]) -> None:
    store = _load_extract()
    store.update(data)
    EXTRACT_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_extract(key: Optional[str] = None):
    store = _load_extract()
    if key is None:
        return store
    return store.get(key)
