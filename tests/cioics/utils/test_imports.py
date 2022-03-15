from pathlib import Path

import cioics
import pytest
from cioics.utils.imports import import_symbol


def test_import_symbol_fn():
    res = import_symbol("numpy.array")
    from numpy import array

    assert res is array


def test_import_symbol_cls():
    res = import_symbol("rich.console.Console")
    from rich.console import Console

    assert res is Console


def test_import_symbol_path():
    file_path = Path(cioics.__file__).parent / "ast" / "nodes.py"
    res = import_symbol(f"{str(file_path)}:SweepNode")
    assert res.__name__ == "SweepNode"


def test_import_symbol_raise():
    with pytest.raises(ImportError):
        import_symbol("rich.console.SomethingThatDoesNotExist")

    with pytest.raises(ImportError):
        import_symbol("file_that_does_not_exist.py:AAAAAA")

    file_path = Path(cioics.__file__).parent / "ast" / "nodes.py"
    with pytest.raises(ImportError):
        import_symbol(f"{str(file_path)}:HolyPinoly")
