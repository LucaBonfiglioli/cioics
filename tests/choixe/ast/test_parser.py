from __future__ import annotations

from typing import Any

import pytest
from choixe.ast.nodes import (
    DateNode,
    DictNode,
    ForNode,
    ImportNode,
    IndexNode,
    InstanceNode,
    ItemNode,
    ListNode,
    ModelNode,
    ObjectNode,
    StrBundleNode,
    SweepNode,
    UuidNode,
    VarNode,
)
from choixe.ast.parser import ChoixeParsingError, ChoixeSyntaxError, parse


class TestParse:
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
        assert parse(expr) == expected

    def test_parse_model(self):
        expr = {
            "$model": "path/to/a/script.py:ModelName",
            "$args": {
                "a": 10,
                "b": {
                    "foo": "hello",
                    "bar": "world",
                },
            },
        }
        expected = ModelNode(
            ObjectNode("path/to/a/script.py:ModelName"),
            DictNode(
                {
                    ObjectNode("a"): ObjectNode(10),
                    ObjectNode("b"): DictNode(
                        {
                            ObjectNode("foo"): ObjectNode("hello"),
                            ObjectNode("bar"): ObjectNode("world"),
                        }
                    ),
                }
            ),
        )
        assert parse(expr) == expected

    def test_parse_for(self):
        expr = {"$for(iterable, x)": {"node_$index(x)": "Hello_$item(x)"}}
        expected = ForNode(
            ObjectNode("iterable"),
            DictNode(
                {
                    StrBundleNode(
                        ObjectNode("node_"), IndexNode(ObjectNode("x"))
                    ): StrBundleNode(ObjectNode("Hello_"), ItemNode(ObjectNode("x")))
                }
            ),
            ObjectNode("x"),
        )
        assert parse(expr) == expected

    def test_parse_for_compact(self):
        expr = {"$for(iterable)": {"node_$index": "Hello_$item"}}
        expected = ForNode(
            ObjectNode("iterable"),
            DictNode(
                {
                    StrBundleNode(ObjectNode("node_"), IndexNode()): StrBundleNode(
                        ObjectNode("Hello_"), ItemNode()
                    )
                }
            ),
        )
        assert parse(expr) == expected


class TestStringParse:
    def test_simple(self):
        expr = "I am a string"
        assert parse(expr) == ObjectNode(expr)

    @pytest.mark.parametrize(
        ["id_", "default", "env"],
        [
            ["var1", 10, False],
            ["var1.var2", "hello", True],
            ["var.var.var", 10.0, True],
        ],
    )
    def test_var(self, id_: Any, default: Any, env: bool):
        default_str = f'"{default}"' if isinstance(default, str) else default
        expr = f"$var({id_}, default={default_str}, env={env})"
        assert parse(expr) == VarNode(
            ObjectNode(id_), default=ObjectNode(default), env=ObjectNode(env)
        )

    def test_import(self):
        path = "path/to/my/file.json"
        expr = f"$import('{path}')"
        assert parse(expr) == ImportNode(ObjectNode(path))

    def test_sweep(self):
        expr = "$sweep(10, foo.bar, '30')"
        expected = SweepNode(ObjectNode(10), ObjectNode("foo.bar"), ObjectNode("30"))
        assert parse(expr) == expected

    def test_str_bundle(self):
        expr = "I am a string with $var(one.two.three) and $sweep(10, foo.bar, '30')"
        expected = StrBundleNode(
            ObjectNode("I am a string with "),
            VarNode(ObjectNode("one.two.three")),
            ObjectNode(" and "),
            SweepNode(ObjectNode(10), ObjectNode("foo.bar"), ObjectNode("30")),
        )
        assert parse(expr) == expected

    def test_uuid(self):
        expr = "$uuid"
        expected = UuidNode()
        assert parse(expr) == expected

    @pytest.mark.parametrize(["format_"], [[None], ["%Y-%m-%d"], ["%h:%M:%s"]])
    def test_date(self, format_):
        expr = "$date"
        if format_ is not None:
            expr += f'("{format_}")'
        format_ = ObjectNode(format_) if format_ is not None else None
        assert parse(expr) == DateNode(format_)


class TestParserRaise:
    def test_unknown_directive(self):
        expr = "$unknown_directive(lots, of, params=10)"
        with pytest.raises(ChoixeParsingError):
            parse(expr)

    def test_arg_too_complex(self):
        expr = "$sweep(lots, of, [arguments, '10'])"
        with pytest.raises(ChoixeParsingError):
            parse(expr)

    @pytest.mark.parametrize(
        ["expr"],
        [
            ["$var(f.dd111])"],
            ["I am a string with $import(ba[a)"],
            ["$var(invalid syntax ::) that raises syntaxerror"],
            ["$a+b a"],
        ],
    )
    def test_syntax_error(self, expr: str):
        with pytest.raises(ChoixeParsingError):
            parse(expr)
