from typing import Any

from choixe.ast.nodes import Node, ObjectNode
from choixe.visitors.unparser import Unparser
import numpy as np


class Decoder(Unparser):
    """Specialization of the `Unparser` for the decode operation."""

    def visit_object(self, node: ObjectNode) -> Any:
        data = super().visit_object(node)
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif "numpy" in str(type(data)):
            return data.item()
        else:
            return data


def decode(node: Node) -> Any:
    """A special unparsing operation that also converts some object types like numpy
    arrays into built-in lists that are supported by common markup formats like yaml and
    json.

    Args:
        node (Node): The Choixe AST node to decode.

    Returns:
        List[Tuple[List[Union[str, int]], Any]]: The decoded unparsed node.
    """
    return node.accept(Decoder())
