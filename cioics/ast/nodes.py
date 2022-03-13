from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence, Union


class NodeVisitor:  # pragma: no cover
    def visit_dict_node(self, node: DictNode) -> Any:
        return node

    def visit_list_node(self, node: ListNode) -> Any:
        return node

    def visit_object_node(self, node: ObjectNode) -> Any:
        return node

    def visit_str_bundle_node(self, node: StrBundleNode) -> Any:
        return node

    def visit_id_node(self, node: IdNode) -> Any:
        return node

    def visit_var_node(self, node: VarNode) -> Any:
        return node

    def visit_env_node(self, node: EnvNode) -> Any:
        return node

    def visit_import_node(self, node: ImportNode) -> Any:
        return node

    def visit_sweep_node(self, node: SweepNode) -> Any:
        return node


class Node(ABC):
    @abstractmethod
    def accept(self, visitor: NodeVisitor) -> Any:  # pragma: no cover
        pass


class DictNode(Node):
    def __init__(self, nodes: dict[Node, Node]) -> None:
        super().__init__()
        self._nodes = nodes

    @property
    def nodes(self) -> dict[Node, Node]:
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_dict_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"DictNode({self.nodes})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, DictNode) and self.nodes == __o.nodes


class ListNode(Node):
    def __init__(self, *nodes: Node) -> None:
        super().__init__()
        self._nodes = nodes

    @property
    def nodes(self) -> list[Node]:
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_list_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ListNode({self.nodes})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, ListNode) and self.nodes == __o.nodes


class ObjectNode(Node):
    def __init__(self, data: Any) -> None:
        super().__init__()
        self._data = data

    @property
    def data(self) -> Any:
        return self._data

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_object_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ObjectNode({self.data})"

    def __hash__(self) -> int:
        return hash(self._data)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, ObjectNode) and self.data == __o.data


class StrBundleNode(Node):
    def __init__(self, *nodes: Node) -> None:
        self._nodes = nodes

    @property
    def nodes(self) -> list[Node]:
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_str_bundle_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"StrBundleNode({self.nodes})"

    def __hash__(self) -> int:
        return hash(tuple(self.nodes))

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, StrBundleNode) and self.nodes == __o.nodes


class IdNode(Node):
    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_id_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"IdNode({self.name})"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, IdNode) and self.name == __o.name


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

    def __repr__(self) -> str:  # pragma: no cover
        return f"VarNode({self.identifier}, {self._default})"

    def __hash__(self) -> int:
        return hash((self.identifier, self.default))

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, VarNode)
            and self.identifier == __o.identifier
            and self.default == __o.default
        )


class EnvNode(VarNode):
    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_env_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"EnvNode({self.identifier}, {self._default})"

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, EnvNode)
            and self.identifier == __o.identifier
            and self.default == __o.default
        )


class ImportNode(Node):
    def __init__(self, path: ObjectNode) -> None:
        super().__init__()
        self._path = path

    @property
    def path(self) -> ObjectNode:
        return self._path

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_import_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ImportNode({self.path})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, ImportNode) and self.path == __o.path


class SweepNode(Node):
    def __init__(self, *cases: Union[ObjectNode, IdNode]) -> None:
        super().__init__()
        self._cases = cases

    @property
    def cases(self) -> Sequence[Union[ObjectNode, IdNode]]:
        return tuple(self._cases)

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_sweep_node(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SweepNode({self.cases})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, SweepNode) and self.cases == __o.cases

    def __hash__(self) -> int:
        return hash(self.cases)
