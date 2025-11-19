import yaml
import os

EXTRACT_FILE = "extract.yaml"

def write_extract(data: dict):
    # 如果文件不存在，先创建
    if not os.path.exists(EXTRACT_FILE):
        with open(EXTRACT_FILE, "w", encoding="utf-8") as f:
            yaml.dump({}, f)
        return write_extract(data)  # 递归调用一次，现在文件已存在
    
    with open(EXTRACT_FILE, "r+", encoding="utf-8") as f:
        try:
            old = yaml.safe_load(f) or {}
        except:
            old = {}
        old.update(data)
        f.seek(0)
        f.truncate()
        yaml.dump(old, f)

def read_extract(key=None):
    if not os.path.exists(EXTRACT_FILE):
        return {} if key is None else None
    with open(EXTRACT_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        return data if key is None else data.get(key)