from typing import Any

from cioics.ast.nodes import ObjectNode
from cioics.visitors.unparser import Unparser


class Decoder(Unparser):
    def visit_object_node(self, node: ObjectNode) -> Any:
        return super().visit_object_node(node)
