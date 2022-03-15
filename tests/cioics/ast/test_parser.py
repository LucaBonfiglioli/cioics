from __future__ import annotations

from typing import Any

import pytest
from cioics.ast.nodes import (
    DictNode,
    EnvNode,
    IdNode,
    ImportNode,
    InstanceNode,
    ListNode,
    ObjectNode,
    StrBundleNode,
    SweepNode,
    VarNode,
)
from cioics.ast.parser import parse


class TestParser:
    def test_parse_dict(self):
        expr = {"a": 10, "b": {"c": 10.0, "d": "hello"}}
        expected = DictNode(
            {
                ObjectNode("a"): ObjectNode(10),
                ObjectNode("b"): DictNode(
                    {
                        ObjectNode("c"): ObjectNode(10.0),
                        ObjectNode("d"): ObjectNode("hello"),
                    }
                ),
            }
        )
        assert parse(expr) == expected

    def test_parse_list(self):
        expr = [1, 2, 3, ("foo", "bar", [10.0, 10])]
        expected = ListNode(
            ObjectNode(1),
            ObjectNode(2),
            ObjectNode(3),
            ListNode(
                ObjectNode("foo"),
                ObjectNode("bar"),
                ListNode(ObjectNode(10.0), ObjectNode(10)),
            ),
        )
        assert parse(expr) == expected

    def test_parse_instance(self):
        expr = {
            "$call": "path/to/a/script.py:ClassName",
            "$args": {
                "a": 10,
                "b": {
                    "$call": "some.interesting.module.MyClass",
                    "$args": {
                        "foo": "hello",
                        "bar": "world",
                    },
                },
            },
        }
        expected = InstanceNode(
            ObjectNode("path/to/a/script.py:ClassName"),
            DictNode(
                {
                    ObjectNode("a"): ObjectNode(10),
                    ObjectNode("b"): InstanceNode(
                        ObjectNode("some.interesting.module.MyClass"),
                        DictNode(
                            {
                                ObjectNode("foo"): ObjectNode("hello"),
                                ObjectNode("bar"): ObjectNode("world"),
                            }
                        ),
                    ),
                }
            ),
        )
        print(parse(expr))
        print(expected)
        assert parse(expr) == expected


class TestStrParser:
    def test_simple(self):
        expr = "I am a string"
        assert parse(expr) == ObjectNode(expr)

    @pytest.mark.parametrize(
        ["id_", "default"],
        [["var1", 10], ["var1.var2", "hello"], ["var.var.var", 10.0]],
    )
    def test_var(self, id_: Any, default: Any):
        default_str = f'"{default}"' if isinstance(default, str) else default
        expr = f"$var({id_}, default={default_str})"
        assert parse(expr) == VarNode(IdNode(id_), default=ObjectNode(default))

    @pytest.mark.parametrize(
        ["id_", "default"],
        [["env1", 42], ["env1.env2", "hello"], ["env.env.env", 25.0]],
    )
    def test_env(self, id_: Any, default: Any):
        default_str = f'"{default}"' if isinstance(default, str) else default
        expr = f"$env({id_}, default={default_str})"
        assert parse(expr) == EnvNode(IdNode(id_), default=ObjectNode(default))

    def test_import(self):
        path = "path/to/my/file.json"
        expr = f"$import('{path}')"
        assert parse(expr) == ImportNode(ObjectNode(path))

    def test_sweep(self):
        expr = "$sweep(10, foo.bar, '30')"
        expected = SweepNode(ObjectNode(10), IdNode("foo.bar"), ObjectNode("30"))
        assert parse(expr) == expected

    def test_str_bundle(self):
        expr = "I am a string with $var(one.two.three) and $sweep(10, foo.bar, '30')"
        expected = StrBundleNode(
            ObjectNode("I am a string with "),
            VarNode(IdNode("one.two.three")),
            ObjectNode(" and "),
            SweepNode(ObjectNode(10), IdNode("foo.bar"), ObjectNode("30")),
        )
        assert parse(expr) == expected

    def test_unknown_directive(self):
        expr = "$unknown_directive(lots, of, params=10)"
        with pytest.raises(NotImplementedError):
            parse(expr)

    def test_arg_too_complex(self):
        expr = "$sweep(lots, of, [arguments, '10'])"
        with pytest.raises(NotImplementedError):
            parse(expr)
