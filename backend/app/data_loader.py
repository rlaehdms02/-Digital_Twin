import json
from pathlib import Path

# backend/app/data_loader.py 기준으로 두 단계 위 = safeexit/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "buildings" / "bldg01" / "2F"


def read_json(filename: str):
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_building() -> dict:
    nodes = read_json("nodes.json")
    edges = read_json("edges.json")
    return {
        "nodes": {n["id"]: n for n in nodes},
        "edges": {e["id"]: e for e in edges},
    }