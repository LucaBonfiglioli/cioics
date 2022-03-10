from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence, Union


class NodeVisitor:
    def visit_dict_node(self, node: DictNode) -> Any:
        pass

    def visit_list_node(self, node: ListNode) -> Any:
        pass

    def visit_object_node(self, node: ObjectNode) -> Any:
        pass

    def visit_str_bundle_node(self, node: StrBundleNode) -> Any:
        pass

    def visit_id_node(self, node: IdNode) -> Any:
        pass

    def visit_var_node(self, node: VarNode) -> Any:
        pass

    def visit_import_node(self, node: ImportNode) -> Any:
        pass

    def visit_sweep_node(self, node: SweepNode) -> Any:
        pass


class Node(ABC):
    @abstractmethod
    def accept(self, visitor: NodeVisitor) -> Any:
        pass


class DictNode(Node):
    def __init__(self, nodes: dict[str, Node]) -> None:
        super().__init__()
        self._nodes = nodes

    @property
    def nodes(self) -> dict[str, Node]:
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_dict_node(self)

    def __repr__(self) -> str:
        return f"DictNode({self.nodes})"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, DictNode):
            return self.nodes == __o.nodes
        return False


class ListNode(Node):
    def __init__(self, nodes: list[Node]) -> None:
        super().__init__()
        self._nodes = nodes

    @property
    def nodes(self) -> list[Node]:
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_list_node(self)

    def __repr__(self) -> str:
        return f"ListNode({self.nodes})"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, ListNode):
            return self.nodes == __o.nodes
        return False


class ObjectNode(Node):
    def __init__(self, data: Any) -> None:
        super().__init__()
        self._data = data

    @property
    def data(self) -> Any:
        return self._data

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_object_node(self)

    def __repr__(self) -> str:
        return f"ObjectNode({self.data})"

    def __hash__(self) -> int:
        return hash(self._data)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, ObjectNode):
            return self.data == __o.data
        return False


class StrBundleNode(Node):
    def __init__(self, *nodes: Node) -> None:
        self._nodes = nodes

    @property
    def nodes(self) -> list[Node]:
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_str_bundle_node(self)

    def __repr__(self) -> str:
        return f"StrBundleNode({self.nodes})"

    def __hash__(self) -> int:
        return hash(tuple(self.nodes))

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, StrBundleNode):
            return self.nodes == __o.nodes
        return False


class IdNode(Node):
    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_id_node(self)

    def __repr__(self) -> str:
        return f"IdNode({self.name})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, IdNode):
            return self.name == __o.name
        return False


class VarNode(Node):
    def __init__(
        self, identifier: IdNode, default: Optional[ObjectNode] = None
    ) -> None:
        super().__init__()
        self._id = identifier
        self._default = default

    @property
    def identifier(self) -> IdNode:
        return self._id

    @property
    def default(self) -> Optional[ObjectNode]:
        return self._default

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_var_node(self)

    def __repr__(self) -> str:
        return f"VarNode({self.identifier})"

    def __hash__(self) -> int:
        return hash((self.identifier, self.default))

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, VarNode):
            return self.identifier == __o.identifier and self.default == __o.default
        return False


class ImportNode(Node):
    def __init__(self, path: ObjectNode) -> None:
        super().__init__()
        self._path = path

    @property
    def path(self) -> ObjectNode:
        return self._path

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_import_node(self)

    def __repr__(self) -> str:
        return f"ImportNode({self.path})"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, ImportNode):
            return self.path == __o.path
        return False


class SweepNode(Node):
    def __init__(self, *cases: Union[ObjectNode, IdNode]) -> None:
        super().__init__()
        self._cases = cases

    @property
    def cases(self) -> Sequence[Union[ObjectNode, IdNode]]:
        return tuple(self._cases)

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_sweep_node(self)

    def __repr__(self) -> str:
        return f"SweepNode({self.cases})"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, SweepNode):
            return self.cases == __o.cases
        return False
