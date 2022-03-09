from typing import Any

from cioics.nodes import (
    DictNode,
    IdNode,
    ImportNode,
    ListNode,
    Node,
    NodeVisitor,
    ObjectNode,
    SweepNode,
    VarNode,
)


class UnparserVisitor(NodeVisitor):
    _ROOT_KEY = "__root__"

    def __init__(self) -> None:
        super().__init__()
        self._data = None

    def visit_dict_node(self, node: DictNode) -> None:
        self._data = {}
        for k, v in node.nodes.items():
            self._data[unparse(k)] = unparse(v)

    def visit_list_node(self, node: ListNode) -> None:
        self._data = []
        for x in node.nodes:
            self._data.append(unparse(x))

    def visit_object_node(self, node: ObjectNode) -> None:
        self._data = node.data

    def visit_id_node(self, node: IdNode) -> None:
        self._data = node.name

    def visit_sweep_node(self, node: SweepNode) -> None:
        body = self._unparse_as_args(*node.cases)
        self._data = f"$sweep({body})"

    def visit_var_node(self, node: VarNode) -> None:
        self._data = f"$var({unparse(node.identifier)})"

    def visit_import_node(self, node: ImportNode) -> None:
        self._data = f'$import("{unparse(node.path)}")'

    def _unparse_as_arg(self, node: Node) -> str:
        unparsed = unparse(node)
        if isinstance(node, ObjectNode):
            if isinstance(unparsed, str):
                return f'"{unparsed}"'
            else:
                return str(unparsed)
        else:
            return str(unparsed)

    def _unparse_as_args(self, *nodes: Node) -> str:
        return ", ".join([self._unparse_as_arg(x) for x in nodes])

    @property
    def data(self) -> Any:
        return self._data


def unparse(node: Node) -> Any:
    visitor = UnparserVisitor()
    node.accept(visitor)
    return visitor.data
