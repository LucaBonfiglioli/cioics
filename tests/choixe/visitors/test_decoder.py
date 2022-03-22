from typing import Any

import numpy as np
import pytest
from choixe.ast.nodes import DictNode, ListNode, Node, ObjectNode
from choixe.visitors import decode
from deepdiff import DeepDiff
from pydantic import BaseModel


class Person(BaseModel):
    id_: str
    age: int


class Cat(BaseModel):
    age: int
    weight: float
    name: str
    owner: Person


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
        [
            ObjectNode(
                Cat(
                    age=10,
                    weight=5.23,
                    name="Oliver",
                    owner=Person(id_="OCJ123j", age=32),
                )
            ),
            {
                "$model": "test_decoder.Cat",
                "$args": {
                    "age": 10,
                    "weight": 5.23,
                    "name": "Oliver",
                    "owner": {
                        "id_": "OCJ123j",
                        "age": 32,
                    },
                },
            },
        ],
    ],
)
def test_decode(node: Node, expected: Any):
    assert not DeepDiff(decode(node), expected)
