import importlib
import uuid
from typing import Any


def import_symbol(symbol_path: str) -> Any:
    try:
        if ":" in symbol_path:
            module_path, _, symbol_name = symbol_path.rpartition(":")
            spec = importlib.util.spec_from_file_location(uuid.uuid4().hex, module_path)
            module_ = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module_)
        else:
            module_path, _, symbol_name = symbol_path.rpartition(".")
            module_ = importlib.import_module(module_path)
        res = getattr(module_, symbol_name)
    except Exception as e:
        raise ImportError(f"Cannot import {symbol_name} from {module_path}") from e
    return res
