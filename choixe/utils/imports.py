import importlib
import importlib.util
import os
import sys
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Optional


class sys_path(ContextDecorator):
    def __init__(self, path: Path):
        self._new_cwd = path

    def __enter__(self):
        sys.path.insert(0, str(self._new_cwd))

    def __exit__(self, exc_type, exc_value, traceback):
        sys.path.pop(0)


def import_symbol(symbol_path: str, cwd: Optional[Path] = None) -> Any:
    cwd = Path(os.getcwd()) if cwd is None else cwd
    try:
        if ":" in symbol_path:
            module_path, _, symbol_name = symbol_path.rpartition(":")

            module_path = Path(module_path)
            if not module_path.is_absolute():
                module_path = cwd / module_path

            with sys_path(module_path.parent):
                id_ = "__main__"
                spec = importlib.util.spec_from_file_location(id_, str(module_path))
                module_ = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module_)
        else:
            module_path, _, symbol_name = symbol_path.rpartition(".")
            module_ = importlib.import_module(module_path)
        res = getattr(module_, symbol_name)
    except Exception as e:
        raise ImportError(f"Cannot import {symbol_name} from {module_path}") from e
    return res
