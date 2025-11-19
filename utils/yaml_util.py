"""Utility helpers for fixtures/extract storage with optional YAML parsing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback to JSON-only parsing
    yaml = None

EXTRACT_FILE = Path("extract.yaml")


def _strip_inline_comment(line: str) -> str:
    cleaned = []
    in_string = False
    string_char = ""
    escape = False
    for char in line:
        if escape:
            cleaned.append(char)
            escape = False
            continue
        if in_string:
            cleaned.append(char)
            if char == "\\":
                escape = True
            elif char == string_char:
                in_string = False
            continue
        if char in ('"', "'"):
            in_string = True
            string_char = char
            cleaned.append(char)
            continue
        if char == "#":
            break
        cleaned.append(char)
    return "".join(cleaned).rstrip()


def _strip_comments(text: str) -> str:
    cleaned_lines = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        processed = _strip_inline_comment(raw_line)
        if processed.strip():
            cleaned_lines.append(processed)
    return "\n".join(cleaned_lines)


def load_data_file(path: str | Path) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return None
    text = file_path.read_text(encoding="utf-8")
    if not text.strip():
        return None
    if yaml is not None:
        try:
            return yaml.safe_load(text)
        except Exception:  # pragma: no cover - defer to JSON for malformed YAML
            pass
    for candidate in (text, _strip_comments(text)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(
        f"无法解析 {path}，请确保其为合法 JSON，或安装 PyYAML 以支持完整 YAML 语法"
    )


def _load_extract() -> Dict[str, Any]:
    data = load_data_file(EXTRACT_FILE)
    return data or {}


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
