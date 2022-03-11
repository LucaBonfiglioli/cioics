from typing import Any

import numpy as np
import pytest
from cioics.ast.nodes import DictNode, ListNode, Node, ObjectNode
from cioics.visitors import decode
from deepdiff import DeepDiff


@pytest.mark.parametrize(
    ["node", "expected"],
    [
        [
            DictNode({ObjectNode("foo"): ObjectNode(np.zeros((2, 3, 2)))}),
            {
                "foo": [
                    [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
                    [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
                ]
            },
        ],
        [
            ListNode(ObjectNode(np.zeros((2, 3, 2)))),
            [
                [
                    [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
                    [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
                ]
            ],
        ],
        [ObjectNode(np.uint8(24)), 24],
        [ObjectNode(np.float64(0.125)), 0.125],
    ],
)
def test_decode(node: Node, expected: Any):
    assert not DeepDiff(decode(node), expected)
