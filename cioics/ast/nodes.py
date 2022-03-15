from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence, Union


class NodeVisitor:  # pragma: no cover
    """Base class for all Choixe visitors. A visitor can be seen as a special recursive
    function that transforms a `Node` (i.e. an element of a syntax tree) into something
    else, depending on the implementation.

    A `NodeVisitor` implements a variation of the Visitor design pattern on a generic
    `Node` object, i.e. an element in the Choixe AST. In particular, visiting methods
    can return values, providing an easier way to use visitors to produce an output.

    This basic node visitor simply forwards the inputs to the outputs, essentially
    performing no operation on the AST.

    All the methods of `NodeVisitor` are called `visit_<node_type>`, they take as input
    the corresponding node object, and they can return anything.
    """

    def visit_dict(self, node: DictNode) -> Any:
        return node

    def visit_list(self, node: ListNode) -> Any:
        return node

    def visit_object(self, node: ObjectNode) -> Any:
        return node

    def visit_str_bundle(self, node: StrBundleNode) -> Any:
        return node

    def visit_id(self, node: IdNode) -> Any:
        return node

    def visit_var(self, node: VarNode) -> Any:
        return node

    def visit_env(self, node: EnvNode) -> Any:
        return node

    def visit_import(self, node: ImportNode) -> Any:
        return node

    def visit_sweep(self, node: SweepNode) -> Any:
        return node

    def visit_instance(self, node: InstanceNode) -> Any:
        return node


class Node(ABC):
    """A generic element of the Choixe AST, all nodes must implement this interface."""

    @abstractmethod
    def accept(self, visitor: NodeVisitor) -> Any:  # pragma: no cover
        """Accepts an incoming visitor. This method should simply call the respective
        `visit_<node_type>` method of the visiting object, pass `self` as argument
        and forward the result.

        Args:
            visitor (NodeVisitor): The visiting object.

        Returns:
            Any: The visitor result.
        """
        pass


class HashNode(Node):
    """A `HashNode` is a special type of node that is hashable. It represents an
    immutable structure and can generally be used as a dictionary key."""

    @abstractmethod
    def _hash(self) -> int:  # pragma: no cover
        """Returns the hash of this object. Called by __hash__ method."""
        pass

    def __hash__(self) -> int:
        return self._hash()

    def __eq__(self, __o: object) -> bool:
        return self.__class__ == __o.__class__ and hash(self) == hash(__o)


class DictNode(Node):
    """AST node for Mapping-like structures. Contains a mapping from `HashNode` to `Node`."""

    def __init__(self, nodes: Dict[HashNode, Node]) -> None:
        super().__init__()
        self._nodes = nodes

    @property
    def nodes(self) -> Dict[HashNode, Node]:
        """Returns a dictionary containing the child nodes."""
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_dict(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"DictNode({self.nodes})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, DictNode) and self.nodes == __o.nodes


class ListNode(Node):
    """AST node for List-like structures. Contains a list of `Node` objects."""

    def __init__(self, *nodes: Node) -> None:
        super().__init__()
        self._nodes = nodes

    @property
    def nodes(self) -> list[Node]:
        """Returns a list containing the child nodes."""
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_list(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ListNode({self.nodes})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, ListNode) and self.nodes == __o.nodes


class ObjectNode(HashNode):
    """An `ObjectNode` contains a single generic hashable python object, like a built-in
    int, float or str."""

    def __init__(self, data: Any) -> None:
        super().__init__()
        self._data = data

    @property
    def data(self) -> Any:
        """Returns the wrapped python object."""
        return self._data

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_object(self)

    def _hash(self) -> int:
        return hash(self._data)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ObjectNode({self.data})"


class StrBundleNode(HashNode):
    """A `StrBundleNode` represents a concatenation of a sequence of strings."""

    def __init__(self, *nodes: ObjectNode) -> None:
        self._nodes = nodes

    @property
    def nodes(self) -> list[ObjectNode]:
        """Returns a list of child objects."""
        return self._nodes

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_str_bundle(self)

    def _hash(self) -> int:
        return hash(tuple(self.nodes))

    def __repr__(self) -> str:  # pragma: no cover
        return f"StrBundleNode({self.nodes})"


class IdNode(HashNode):
    """An `IdNode` represents the id of a variable."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        """Returns the id of this variable."""
        return self._name

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_id(self)

    def _hash(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:  # pragma: no cover
        return f"IdNode({self.name})"


class VarNode(HashNode):
    """A `VarNode` represents a Choixe variable. It has an id and a default value."""

    def __init__(
        self, identifier: IdNode, default: Optional[ObjectNode] = None
    ) -> None:
        super().__init__()
        self._id = identifier
        self._default = default

    @property
    def identifier(self) -> IdNode:
        """Returns the id node of this variable."""
        return self._id

    @property
    def default(self) -> Optional[ObjectNode]:
        """Returns the default object node of this variable."""
        return self._default

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_var(self)

    def _hash(self) -> int:
        return hash((self.identifier, self.default))

    def __repr__(self) -> str:  # pragma: no cover
        return f"VarNode({self.identifier}, {self._default})"


class EnvNode(VarNode):
    """An `EnvNode` represents a Choixe environment variable. It is a special type of
    variable and therefore, it has an id and a default value."""

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_env(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"EnvNode({self.identifier}, {self._default})"


class ImportNode(Node):
    """An `ImportNode` represents a Choixe import directive from a filesystem path."""

    def __init__(self, path: ObjectNode) -> None:
        super().__init__()
        self._path = path

    @property
    def path(self) -> ObjectNode:
        """Returns the object node containing the filesystem path."""
        return self._path

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_import(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ImportNode({self.path})"

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, ImportNode) and self.path == __o.path


class SweepNode(HashNode):
    """A `SweepNode` represents a Choixe sweep directive from multiple branching opions."""

    def __init__(self, *cases: Union[ObjectNode, IdNode]) -> None:
        super().__init__()
        self._cases = cases

    @property
    def cases(self) -> Sequence[Union[ObjectNode, IdNode]]:
        """Returns a tuple containing all the possible options."""
        return tuple(self._cases)

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_sweep(self)

    def _hash(self) -> int:
        return hash(self.cases)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SweepNode({self.cases})"


class InstanceNode(Node):
    """An `InstanceNode` represents a Choixe instance block to get the result of a
    generic python callable object."""

    def __init__(self, symbol: ObjectNode, args: DictNode) -> None:
        super().__init__()
        self._symbol = symbol
        self._args = args

    @property
    def symbol(self) -> ObjectNode:
        """Getter for the callable symbol"""
        return self._symbol

    @property
    def args(self) -> DictNode:
        """Getter for the callable arguments"""
        return self._args

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_instance(self)

    def __repr__(self) -> str:  # pragma: no cover
        return f"InstanceNode({self.symbol}, {self.args})"

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, InstanceNode)
            and self.symbol == __o.symbol
            and self.args == __o.args
        )


class ForNode(Node):
    def __init__(
        self, iterable: IdNode, identifier: IdNode, mode: IdNode = IdNode("list")
    ) -> None:
        super().__init__()
        self._iterable = iterable
        self._identifier = identifier
        self._mode = mode

    @property
    def iterable(self) -> IdNode:
        return self._iterable

    @property
    def identifier(self) -> IdNode:
        return self._identifier

    @property
    def mode(self) -> IdNode:
        return self._mode

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_for(self)

    def __repr__(self) -> str:
        return f"ForNode({self.iterable}, {self.identifier}, {self.mode})"

    def __eq__(self, __o: object) -> bool:
        return (
            isinstance(__o, ForNode)
            and __o.iterable == self.iterable
            and __o.identifier == self.identifier
            and __o.mode == self.mode
        )


class IndexNode(HashNode):
    def __init__(self, identifier: IdNode) -> None:
        super().__init__()
        self._identifier = identifier

    @property
    def identifier(self) -> IdNode:
        return self._identifier

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_index(self)

    def _hash(self) -> int:
        return hash(self.identifier)

    def __repr__(self) -> str:  # pragma: no cover
        return f"IndexNode({self.identifier})"


class ItemNode(HashNode):
    def __init__(self, identifier: IdNode) -> None:
        super().__init__()
        self._identifier = identifier

    @property
    def identifier(self) -> IdNode:
        return self._identifier

    def accept(self, visitor: NodeVisitor) -> Any:
        return visitor.visit_item(self)

    def _hash(self) -> int:
        return hash(self.identifier)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ItemNode({self.identifier})"
