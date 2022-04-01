from typing import Any

import pytest
from choixe.ast.nodes import (
    CmdNode,
    DateNode,
    DictNode,
    ForNode,
    ImportNode,
    IndexNode,
    InstanceNode,
    ItemNode,
    ListNode,
    ModelNode,
    Node,
    ObjectNode,
    StrBundleNode,
    SweepNode,
    UuidNode,
    VarNode,
)
from choixe.visitors import unparse
from deepdiff import DeepDiff


@pytest.mark.parametrize(
    ["node", "expected"],
    [
        [ObjectNode(10), 10],
        [ObjectNode(0.124), 0.124],
        [ObjectNode("hello"), "hello"],
        [ObjectNode("my_var"), "my_var"],
        [
            VarNode(ObjectNode("variable.one")),
            "$var(variable.one)",
        ],
        [
            VarNode(ObjectNode("variable.one"), env=ObjectNode(True)),
            "$var(variable.one, env=True)",
        ],
        [
            VarNode(ObjectNode("variable.one"), default=ObjectNode(-24)),
            "$var(variable.one, default=-24)",
        ],
        [
            VarNode(
                ObjectNode("variable.one"),
                default=ObjectNode(-24),
                env=ObjectNode(True),
            ),
            "$var(variable.one, default=-24, env=True)",
        ],
        [ImportNode(ObjectNode("path/to/file.yaml")), '$import("path/to/file.yaml")'],
        [
            SweepNode(ObjectNode("a"), ObjectNode("variable"), ObjectNode(10)),
            "$sweep(a, variable, 10)",
        ],
        [StrBundleNode(ObjectNode("alice")), "alice"],
        [
            StrBundleNode(
                ObjectNode("alice "),
                VarNode(ObjectNode("foo"), default=ObjectNode("loves")),
                ObjectNode(" bob"),
            ),
            "alice $var(foo, default=loves) bob",
        ],
        [
            DictNode(
                {
                    ObjectNode("key1"): ObjectNode(10),
                    ObjectNode("key2"): DictNode(
                        {
                            ObjectNode("key1"): ObjectNode(10.2),
                            ObjectNode("key2"): ObjectNode("hello"),
                        }
                    ),
                }
            ),
            {"key1": 10, "key2": {"key1": 10.2, "key2": "hello"}},
        ],
        [
            DictNode(
                {
                    StrBundleNode(
                        VarNode(ObjectNode("var")), ObjectNode("foo")
                    ): ObjectNode("bar")
                }
            ),
            {"$var(var)foo": "bar"},
        ],
        [
            ListNode(ObjectNode(10), ObjectNode(-0.25), ListNode(ObjectNode("aa"))),
            [10, -0.25, ["aa"]],
        ],
        [
            InstanceNode(
                ObjectNode("path/to_my/file.py:MyClass"),
                DictNode(
                    {
                        ObjectNode("arg1"): InstanceNode(
                            ObjectNode("module.submodule.function"),
                            DictNode(
                                {
                                    ObjectNode("a"): ListNode(
                                        ObjectNode(1), ObjectNode(2)
                                    ),
                                    ObjectNode("b"): ObjectNode(100),
                                }
                            ),
                        )
                    }
                ),
            ),
            {
                "$call": "path/to_my/file.py:MyClass",
                "$args": {
                    "arg1": {
                        "$call": "module.submodule.function",
                        "$args": {"a": [1, 2], "b": 100},
                    }
                },
            },
        ],
        [
            ModelNode(
                ObjectNode("path/to_my/file.py:MyModel"),
                DictNode(
                    {
                        ObjectNode("arg1"): DictNode(
                            {
                                ObjectNode("a"): ListNode(ObjectNode(1), ObjectNode(2)),
                                ObjectNode("b"): ObjectNode(100),
                            }
                        ),
                    }
                ),
            ),
            {
                "$model": "path/to_my/file.py:MyModel",
                "$args": {"arg1": {"a": [1, 2], "b": 100}},
            },
        ],
        [
            ForNode(
                ObjectNode("my.var"),
                DictNode(
                    {
                        ObjectNode("Hello"): ObjectNode("World"),
                        StrBundleNode(
                            ObjectNode("Number_"), IndexNode(ObjectNode("x"))
                        ): ItemNode(ObjectNode("x")),
                    }
                ),
                ObjectNode("x"),
            ),
            {"$for(my.var, x)": {"Hello": "World", "Number_$index(x)": "$item(x)"}},
        ],
        [
            ForNode(
                ObjectNode("my.var"),
                DictNode(
                    {
                        ObjectNode("Hello"): ObjectNode("World"),
                        StrBundleNode(ObjectNode("Number_"), IndexNode()): ItemNode(),
                    }
                ),
            ),
            {"$for(my.var)": {"Hello": "World", "Number_$index": "$item"}},
        ],
        [UuidNode(), "$uuid"],
        [DateNode(), "$date"],
        [DateNode(ObjectNode("%Y%m%d")), '$date("%Y%m%d")'],
        [CmdNode(ObjectNode("ls -lha")), '$cmd("ls -lha")'],
    ],
)
def test_unparse(node: Node, expected: Any):
    assert not DeepDiff(unparse(node), expected)
