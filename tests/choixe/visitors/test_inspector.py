import os
from pathlib import Path

import pytest
from choixe.ast.parser import parse
from choixe.visitors import Inspection, inspect


class TestInspector:
    @pytest.mark.parametrize(
        ["expr", "expected"],
        [
            [{"a": 10, "b": {"a": 20.0}}, Inspection(processed=True)],
            [
                {
                    "$var(variable.one)": 10,
                    "b": "$var(variable.two, default=10.2)",
                    "c": "$var(variable.three, env=True)",
                },
                Inspection(
                    variables={"variable": {"one": None, "two": 10.2, "three": None}},
                    environ={"variable.three": None},
                ),
            ],
            [
                [
                    "$var(variable.one)",
                    "$var(variable.two, default=10.2)",
                    "$var(variable.three, env=True)",
                ],
                Inspection(
                    variables={"variable": {"one": None, "two": 10.2, "three": None}},
                    environ={"variable.three": None},
                ),
            ],
            [
                "String with $var(variable.one) $var(variable.two, default=10.2) $var(variable.three, env=True)",
                Inspection(
                    variables={"variable": {"one": None, "two": 10.2, "three": None}},
                    environ={"variable.three": None},
                ),
            ],
            [
                "$sweep(10, x, variable.x)",
                Inspection(variables={"x": None, "variable": {"x": None}}),
            ],
            [
                {"$call": "numpy.array", "$args": {"shape": [4, 3, 2]}},
                Inspection(symbols={"numpy.array"}),
            ],
            [
                {"$model": "path/to/my_file.py:MyModel", "$args": {"shape": [4, 3, 2]}},
                Inspection(symbols={"path/to/my_file.py:MyModel"}),
            ],
            [
                {"$for(var.x.y, x)": {"$index(x)": "$item(x)"}},
                Inspection(variables={"var": {"x": {"y": None}}}),
            ],
        ],
    )
    def test_inspector(self, expr, expected):
        assert inspect(parse(expr)) == expected

    def test_relative_import(self, plain_cfg):
        data = {"a": "$import('plain_cfg.yml')", "b": {"c": "$import('plain_cfg.yml')"}}
        expected = Inspection(imports={plain_cfg})
        assert inspect(parse(data), cwd=plain_cfg.parent) == expected

    def test_import_not_found(self):
        data = {"a": "$import('nonexisting.yml')"}
        expected = Inspection(imports={Path("nonexisting.yml").absolute()})
        with pytest.warns(UserWarning):
            assert inspect(parse(data)) == expected
