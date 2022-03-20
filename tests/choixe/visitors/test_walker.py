from typing import Any

import pytest
from choixe.ast.nodes import (
    DictNode,
    ListNode,
    Node,
    ObjectNode,
    StrBundleNode,
    VarNode,
    IdNode,
)
from choixe.visitors import walk
from deepdiff import DeepDiff


@pytest.mark.parametrize(
    ["node", "expected"],
    [
        [ObjectNode(10), [([], 10)]],
        [
            StrBundleNode(
                ObjectNode("alice "),
                VarNode(IdNode("foo"), default=ObjectNode("loves")),
                ObjectNode(" bob"),
            ),
            [([], 'alice $var(foo, default="loves") bob')],
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
            [(["key1"], 10), (["key2", "key1"], 10.2), (["key2", "key2"], "hello")],
        ],
        [
            ListNode(ObjectNode(10), ObjectNode(-0.25), ListNode(ObjectNode("aa"))),
            [([0], 10), ([1], -0.25), ([2, 0], "aa")],
        ],
    ],
)
def test_walk(node: Node, expected: Any):
    assert not DeepDiff(walk(node), expected)
