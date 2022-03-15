from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Union

from cioics.ast.parser import parse
from cioics.utils.io import load
from cioics.visitors import process
from deepdiff import DeepDiff


# @dataclass(eq=True)
# class MyCompositeClass:
#     a: Union[MyCompositeClass, int]
#     b: Union[MyCompositeClass, int]


class MyCompositeClass:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, __o: object) -> bool:
        return __o.a == self.a and __o.b == self.b


class TestProcessor:
    context = {"color": {"hue": "red"}, "animal": "cow"}
    env = {"color.hue": "yellow", "animal": "snake"}

    def _expectation_test(self, data, expected, allow_branching: bool = True) -> None:
        for k, v in self.env.items():
            os.environ[k] = v

        try:
            parsed = parse(data)
            res = process(parsed, context=self.context, allow_branching=allow_branching)
            [print(x) for x in res]
            assert not DeepDiff(res, expected)

        finally:
            for k in self.env:
                del os.environ[k]

    def test_var_plain(self):
        data = "$var(color.hue, default='blue')"
        expected = ["red"]
        self._expectation_test(data, expected)

    def test_var_missing(self):
        data = "$var(color.sat, default='low')"
        expected = ["low"]
        self._expectation_test(data, expected)

    def test_var_str_bundle(self):
        data = {"a": "I am a $var(color.hue) $var(animal)"}
        expected = [{"a": "I am a red cow"}]
        self._expectation_test(data, expected)

    def test_env_plain(self):
        data = "$env(color.hue, default='blue')"
        expected = ["yellow"]
        self._expectation_test(data, expected)

    def test_env_missing(self):
        data = "$env(color.sat, default=25)"
        expected = [25]
        self._expectation_test(data, expected)

    def test_env_str_bundle(self):
        data = {"a": "I am a $env(color.hue) $env(animal)"}
        expected = [{"a": "I am a yellow snake"}]
        self._expectation_test(data, expected)

    def test_import_plain(self, plain_cfg: Path):
        path_str = str(PurePosixPath(plain_cfg)).replace("\\", "/")  # Windows please...
        print(path_str)
        data = {"a": f'$import("{path_str}")'}
        expected = [{"a": load(plain_cfg)}]
        self._expectation_test(data, expected)

    def test_import_relative(self, plain_cfg: Path):
        prev_cwd = os.getcwd()
        os.chdir(plain_cfg.parent)
        try:
            data = {"a": f'$import("{plain_cfg.name}")'}
            expected = [{"a": load(plain_cfg)}]
            self._expectation_test(data, expected)
        finally:
            os.chdir(prev_cwd)

    def test_sweep_base(self):
        data = {
            "a": "$sweep(1096, 20.0, '40', color.hue)",
            "b": {
                "a": "$sweep('hello')",
                "b": "$sweep('hello', 'world')",
                "c": "$sweep('hello', 'world')",
                "d": 10,
            },
        }
        expected = [
            {"a": 1096, "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": "red", "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": 1096, "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": "red", "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": 1096, "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": "red", "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": 1096, "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
            {"a": "red", "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
        ]
        self._expectation_test(data, expected)

    def test_sweep_no_branching(self):
        data = {
            "a": '$sweep(1096, 20.0, "40", color.hue)',
            "b": {
                "a": '$sweep("hello")',
                "b": '$sweep("hello", "world")',
                "c": '$sweep("hello", "world")',
                "d": 10,
            },
        }
        self._expectation_test(data, [data], allow_branching=False)

    def test_sweep_lists(self):
        data = ["$sweep(10, 20)", {"a": [10, "$sweep(30, 40)"]}]
        expected = [
            [10, {"a": [10, 30]}],
            [20, {"a": [10, 30]}],
            [10, {"a": [10, 40]}],
            [20, {"a": [10, 40]}],
        ]
        self._expectation_test(data, expected)

    def test_sweep_str_bundle(self):
        data = {"a": "I am a $sweep('red', 'blue') $sweep('sheep', 'cow')"}
        expected = [
            {"a": "I am a red sheep"},
            {"a": "I am a blue sheep"},
            {"a": "I am a red cow"},
            {"a": "I am a blue cow"},
        ]
        self._expectation_test(data, expected)

    def test_sweep_multikey(self):
        data = {
            "$sweep('foo', 'bar')": "$sweep('alice', 'bob')",
            "$sweep('alpha', 'beta')": "$sweep(10, 20)",
        }
        expected = [
            {"foo": "alice", "alpha": 10},
            {"foo": "bob", "alpha": 10},
            {"bar": "alice", "alpha": 10},
            {"bar": "bob", "alpha": 10},
            {"foo": "alice", "alpha": 20},
            {"foo": "bob", "alpha": 20},
            {"bar": "alice", "alpha": 20},
            {"bar": "bob", "alpha": 20},
            {"foo": "alice", "beta": 10},
            {"foo": "bob", "beta": 10},
            {"bar": "alice", "beta": 10},
            {"bar": "bob", "beta": 10},
            {"foo": "alice", "beta": 20},
            {"foo": "bob", "beta": 20},
            {"bar": "alice", "beta": 20},
            {"bar": "bob", "beta": 20},
        ]
        self._expectation_test(data, expected)

    def test_instance(self):
        data = {
            "$call": f"{__file__}:MyCompositeClass",
            "$args": {
                "a": {
                    "$call": f"{__file__}:MyCompositeClass",
                    "$args": {
                        "a": 10,
                        "b": 20,
                    },
                },
                "b": {
                    "$call": f"{__file__}:MyCompositeClass",
                    "$args": {
                        "a": {
                            "$call": f"{__file__}:MyCompositeClass",
                            "$args": {
                                "a": 30,
                                "b": 40,
                            },
                        },
                        "b": {
                            "$call": f"{__file__}:MyCompositeClass",
                            "$args": {
                                "a": 50,
                                "b": 60,
                            },
                        },
                    },
                },
            },
        }
        expected = [
            MyCompositeClass(
                MyCompositeClass(10, 20),
                MyCompositeClass(MyCompositeClass(30, 40), MyCompositeClass(50, 60)),
            )
        ]
        assert process(parse(data)) == expected
