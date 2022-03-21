import importlib
import importlib.util
import os
import sys
from contextlib import ContextDecorator
from pathlib import Path
from types import ModuleType
from typing import Any, Optional
from uuid import uuid1


class sys_path(ContextDecorator):
    """sys_path context decorator that temporarily adds a path to sys.path"""

    def __init__(self, path: Path) -> None:
        self._new_cwd = path

    def __enter__(self) -> None:
        sys.path.insert(0, str(self._new_cwd))

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        sys.path.pop(0)


class sys_module(ContextDecorator):
    """
    ☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️\n
    THIS IS A HACK TO ALLOW DYNAMIC IMPORT FROM FILES CONTAINING DATACLASSES.
    THE USAGE OF THIS DECORATOR SHOULD BE AVOIDED AS IT COULD POTENTIALLY BREAK STUFF.

    THIS DECORATOR IS CURRENTLY USED ONLY IN THIS MODULE AND WE PLAN TO REMOVE IT AS
    SOON AS A BETTER SOLUTION IS FOUND.
    ☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️\n

    sys_module context decorator that temporarily adds a module to sys.modules
    """

    def __init__(self, module: ModuleType, id_: str) -> None:
        self._module = module
        self._id_ = id_

    def __enter__(self) -> None:
        if self._id_ in sys.modules:  # pragma: no cover
            raise RuntimeError(f"Attempted to overwrite system module {self._id_}")

        sys.modules[self._id_] = self._module

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        sys.modules.pop(self._id_)


def import_symbol(symbol_path: str, cwd: Optional[Path] = None) -> Any:
    """Dynamically imports a given symbol. A symbol can be either:

    - A filesystem path followed by the name of an object to import, like:
        "path/to/my_file.py:MyClass"

    - A python module path, like "module.submodule.MyClass"

    Anything can be imported: modules, classes, functions, etc...

    Args:
        symbol_path (str): The symbol to import
        cwd (Optional[Path], optional): The current working directory to resolve
        relative imports. If None, the system cwd will be used. Defaults to None.

    Raises:
        ImportError: If anything goes wrong with the import.

    Returns:
        Any: The dynamically imported object.
    """
    cwd = Path(os.getcwd()) if cwd is None else cwd
    try:
        if ":" in symbol_path:
            module_path, _, symbol_name = symbol_path.rpartition(":")

            module_path = Path(module_path)
            if not module_path.is_absolute():
                module_path = cwd / module_path

            with sys_path(module_path.parent):
                id_ = str(uuid1())
                spec = importlib.util.spec_from_file_location(id_, str(module_path))
                module_ = importlib.util.module_from_spec(spec)
                with sys_module(module_, id_):
                    spec.loader.exec_module(module_)
        else:
            module_path, _, symbol_name = symbol_path.rpartition(".")
            module_ = importlib.import_module(module_path)
        res = getattr(module_, symbol_name)
    except Exception as e:
        raise ImportError(f"Cannot import {symbol_name} from {module_path}") from e
    return res
