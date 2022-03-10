from typing import Any

from cioics.ast.nodes import Node, ObjectNode
from cioics.visitors.unparser import Unparser
import numpy as np


class Decoder(Unparser):
    def visit_object_node(self, node: ObjectNode) -> Any:
        data = super().visit_object_node(node)
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif "numpy" in str(type(data)):
            return data.item()
        else:
            return data


def decode(node: Node) -> Any:
    return node.accept(Decoder())
