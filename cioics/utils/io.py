import json
from pathlib import Path
from typing import Any

import yaml


def get_extension(path: Path) -> str:
    return path.name.split(".")[-1]


def load(path: Path) -> Any:
    ext = get_extension(path)
    if ext in ["yaml", "yml"]:
        return yaml.safe_load(open(path, "r"))
    elif ext in ["json"]:
        return json.load(path)


def dump(obj: Any, path: Path) -> None:
    ext = get_extension(path)
    if ext in ["yaml", "yml"]:
        yaml.safe_dump(obj, open(path, "w"))
    elif ext in ["json"]:
        json.dump(obj, open(path, "w"))
