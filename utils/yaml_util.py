import yaml
import os

EXTRACT_FILE = "extract.yaml"

def write_extract(data: dict):
    with open(EXTRACT_FILE, "r+", encoding="utf-8") as f:
        try:
            old = yaml.safe_load(f) or {}
        except:
            old = {}
        old.update(data)
        f.seek(0)
        yaml.dump(old, f)

def read_extract(key=None):
    if not os.path.exists(EXTRACT_FILE):
        return {} if key is None else None
    with open(EXTRACT_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        return data if key is None else data.get(key)