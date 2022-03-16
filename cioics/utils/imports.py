from contextlib import ContextDecorator
import importlib
import os
import sys
import uuid
from pathlib import Path
from typing import Any


class sys_path(ContextDecorator):
    def __init__(self, path: Path):
        self._new_cwd = path

    def __enter__(self):
        sys.path.insert(0, str(self._new_cwd))

    def __exit__(self, exc_type, exc_value, traceback):
        sys.path.pop(0)


def import_symbol(symbol_path: str) -> Any:
    try:
        if ":" in symbol_path:
            module_path, _, symbol_name = symbol_path.rpartition(":")
            module_path = str(Path(module_path).resolve())
            with sys_path(Path(module_path).parent):
                id_ = uuid.uuid4().hex
                spec = importlib.util.spec_from_file_location(id_, module_path)
                module_ = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module_)
        else:
            module_path, _, symbol_name = symbol_path.rpartition(".")
            module_ = importlib.import_module(module_path)
        res = getattr(module_, symbol_name)
    except Exception as e:
        raise ImportError(f"Cannot import {symbol_name} from {module_path}") from e
    return res
