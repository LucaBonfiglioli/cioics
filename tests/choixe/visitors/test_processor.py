from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

from choixe.ast.parser import parse
from choixe.utils.io import load
from choixe.visitors import process
from deepdiff import DeepDiff


class MyCompositeClass:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, __o: object) -> bool:
        return __o.a == self.a and __o.b == self.b


class TestProcessor:
    context = {
        "color": {"hue": "red"},
        "animal": "cow",
        "collection1": list(range(1000, 1010)),
        "collection2": [str(x) for x in range(100, 105)],
        "collection3": list(range(50, 52)),
        "collection4": [str(x) for x in range(100, 102)],
    }
    env = {"VAR1": "yellow", "VAR2": "snake"}

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
        data = "$var(VAR1, default='blue', env=True)"
        expected = ["yellow"]
        self._expectation_test(data, expected)

    def test_env_missing(self):
        data = "$var(color.sat, default=25, env=True)"
        expected = [25]
        self._expectation_test(data, expected)

    def test_env_str_bundle(self):
        data = {"a": "I am a $var(VAR1, env=True) $var(VAR2, env=True)"}
        expected = [{"a": "I am a yellow snake"}]
        self._expectation_test(data, expected)

    def test_import_plain(self, plain_cfg: Path):
        path_str = str(PurePosixPath(plain_cfg)).replace("\\", "/")  # Windows please...
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

    def test_for_dict(self):
        data = {"$for(collection1, x)": {"Index=$index(x)": "Item=$item(x)"}}
        expected = [
            {
                f"Index={i}": f"Item={x}"
                for i, x in enumerate(self.context["collection1"])
            }
        ]
        self._expectation_test(data, expected)

    def test_for_list(self):
        data = {"$for(collection2, x)": ["$index(x)->$item(x)", 10]}
        expected = [[]]
        [
            expected[0].extend([f"{i}->{x}", 10])
            for i, x in enumerate(self.context["collection2"])
        ]
        self._expectation_test(data, expected)

    def test_for_str(self):
        data = {"$for(collection2, x)": "$index(x)->$item(x)"}
        expected = [
            "".join([f"{i}->{x}" for i, x in enumerate(self.context["collection2"])])
        ]
        self._expectation_test(data, expected)

    def test_for_nested(self):
        data = {
            "$for(collection3, x)": {
                "item_$index(x)=$item(x)": {
                    "$for(collection4, y)": ["item_$index(x)_$index(y)=$item(y)"]
                }
            }
        }
        expected = [
            {
                "item_0=50": ["item_0_0=100", "item_0_1=101"],
                "item_1=51": ["item_1_0=100", "item_1_1=101"],
            }
        ]
        self._expectation_test(data, expected)

    def test_for_sweep(self):
        data = {"$for(collection3, x)": {"$index(x)": "$item(x)=$sweep('a', 'b')"}}
        expected = [
            {0: "50=a", 1: "51=a"},
            {0: "50=a", 1: "51=b"},
            {0: "50=b", 1: "51=a"},
            {0: "50=b", 1: "51=b"},
        ]
        self._expectation_test(data, expected)

    def test_for_mindfuck(self):
        data = {
            "$for(collection3, x)": [
                "$sweep(1, 2)$item(x)",
                {"$for(collection4, y)": ["$sweep(3, 4)$index(x)$item(y)"]},
            ]
        }
        expected = [
            ["150", ["30100", "30101"], "151", ["31100", "31101"]],
            ["150", ["30100", "30101"], "251", ["31100", "31101"]],
            ["150", ["30100", "30101"], "151", ["31100", "41101"]],
            ["150", ["30100", "30101"], "251", ["31100", "41101"]],
            ["150", ["30100", "30101"], "151", ["41100", "31101"]],
            ["150", ["30100", "30101"], "251", ["41100", "31101"]],
            ["150", ["30100", "30101"], "151", ["41100", "41101"]],
            ["150", ["30100", "30101"], "251", ["41100", "41101"]],
            ["250", ["30100", "30101"], "151", ["31100", "31101"]],
            ["250", ["30100", "30101"], "251", ["31100", "31101"]],
            ["250", ["30100", "30101"], "151", ["31100", "41101"]],
            ["250", ["30100", "30101"], "251", ["31100", "41101"]],
            ["250", ["30100", "30101"], "151", ["41100", "31101"]],
            ["250", ["30100", "30101"], "251", ["41100", "31101"]],
            ["250", ["30100", "30101"], "151", ["41100", "41101"]],
            ["250", ["30100", "30101"], "251", ["41100", "41101"]],
            ["150", ["30100", "40101"], "151", ["31100", "31101"]],
            ["150", ["30100", "40101"], "251", ["31100", "31101"]],
            ["150", ["30100", "40101"], "151", ["31100", "41101"]],
            ["150", ["30100", "40101"], "251", ["31100", "41101"]],
            ["150", ["30100", "40101"], "151", ["41100", "31101"]],
            ["150", ["30100", "40101"], "251", ["41100", "31101"]],
            ["150", ["30100", "40101"], "151", ["41100", "41101"]],
            ["150", ["30100", "40101"], "251", ["41100", "41101"]],
            ["250", ["30100", "40101"], "151", ["31100", "31101"]],
            ["250", ["30100", "40101"], "251", ["31100", "31101"]],
            ["250", ["30100", "40101"], "151", ["31100", "41101"]],
            ["250", ["30100", "40101"], "251", ["31100", "41101"]],
            ["250", ["30100", "40101"], "151", ["41100", "31101"]],
            ["250", ["30100", "40101"], "251", ["41100", "31101"]],
            ["250", ["30100", "40101"], "151", ["41100", "41101"]],
            ["250", ["30100", "40101"], "251", ["41100", "41101"]],
            ["150", ["40100", "30101"], "151", ["31100", "31101"]],
            ["150", ["40100", "30101"], "251", ["31100", "31101"]],
            ["150", ["40100", "30101"], "151", ["31100", "41101"]],
            ["150", ["40100", "30101"], "251", ["31100", "41101"]],
            ["150", ["40100", "30101"], "151", ["41100", "31101"]],
            ["150", ["40100", "30101"], "251", ["41100", "31101"]],
            ["150", ["40100", "30101"], "151", ["41100", "41101"]],
            ["150", ["40100", "30101"], "251", ["41100", "41101"]],
            ["250", ["40100", "30101"], "151", ["31100", "31101"]],
            ["250", ["40100", "30101"], "251", ["31100", "31101"]],
            ["250", ["40100", "30101"], "151", ["31100", "41101"]],
            ["250", ["40100", "30101"], "251", ["31100", "41101"]],
            ["250", ["40100", "30101"], "151", ["41100", "31101"]],
            ["250", ["40100", "30101"], "251", ["41100", "31101"]],
            ["250", ["40100", "30101"], "151", ["41100", "41101"]],
            ["250", ["40100", "30101"], "251", ["41100", "41101"]],
            ["150", ["40100", "40101"], "151", ["31100", "31101"]],
            ["150", ["40100", "40101"], "251", ["31100", "31101"]],
            ["150", ["40100", "40101"], "151", ["31100", "41101"]],
            ["150", ["40100", "40101"], "251", ["31100", "41101"]],
            ["150", ["40100", "40101"], "151", ["41100", "31101"]],
            ["150", ["40100", "40101"], "251", ["41100", "31101"]],
            ["150", ["40100", "40101"], "151", ["41100", "41101"]],
            ["150", ["40100", "40101"], "251", ["41100", "41101"]],
            ["250", ["40100", "40101"], "151", ["31100", "31101"]],
            ["250", ["40100", "40101"], "251", ["31100", "31101"]],
            ["250", ["40100", "40101"], "151", ["31100", "41101"]],
            ["250", ["40100", "40101"], "251", ["31100", "41101"]],
            ["250", ["40100", "40101"], "151", ["41100", "31101"]],
            ["250", ["40100", "40101"], "251", ["41100", "31101"]],
            ["250", ["40100", "40101"], "151", ["41100", "41101"]],
            ["250", ["40100", "40101"], "251", ["41100", "41101"]],
        ]
        self._expectation_test(data, expected)
