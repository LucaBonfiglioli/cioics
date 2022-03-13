from typing import Any

import pytest
from cioics.ast.nodes import (
    DictNode,
    EnvNode,
    IdNode,
    ImportNode,
    ListNode,
    Node,
    ObjectNode,
    StrBundleNode,
    SweepNode,
    VarNode,
)
from cioics.visitors import unparse
from deepdiff import DeepDiff


@pytest.mark.parametrize(
    ["node", "expected"],
    [
        [ObjectNode(10), 10],
        [ObjectNode(0.124), 0.124],
        [ObjectNode("hello"), "hello"],
        [IdNode("my_var"), "my_var"],
        [
            VarNode(IdNode("variable.one")),
            "$var(variable.one)",
        ],
        [
            EnvNode(IdNode("variable.one")),
            "$env(variable.one)",
        ],
        [
            VarNode(IdNode("variable.one"), default=ObjectNode(-24)),
            "$var(variable.one, default=-24)",
        ],
        [
            EnvNode(IdNode("variable.one"), default=ObjectNode(-24)),
            "$env(variable.one, default=-24)",
        ],
        [ImportNode(ObjectNode("path/to/file.yaml")), '$import("path/to/file.yaml")'],
        [
            SweepNode(ObjectNode("a"), IdNode("variable"), ObjectNode(10)),
            '$sweep("a", variable, 10)',
        ],
        [StrBundleNode(ObjectNode("alice")), "alice"],
        [
            StrBundleNode(
                ObjectNode("alice "),
                VarNode(IdNode("foo"), default=ObjectNode("loves")),
                ObjectNode(" bob"),
            ),
            'alice $var(foo, default="loves") bob',
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
                        VarNode(IdNode("var")), ObjectNode("foo")
                    ): ObjectNode("bar")
                }
            ),
            {"$var(var)foo": "bar"},
        ],
        [
            ListNode(ObjectNode(10), ObjectNode(-0.25), ListNode(ObjectNode("aa"))),
            [10, -0.25, ["aa"]],
        ],
    ],
)
def test_unparse(node: Node, expected: Any):
    assert not DeepDiff(unparse(node), expected)
