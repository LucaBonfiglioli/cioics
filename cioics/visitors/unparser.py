from typing import Any, Dict, List

from cioics.ast.nodes import (
    DictNode,
    EnvNode,
    IdNode,
    ImportNode,
    ListNode,
    Node,
    NodeVisitor,
    ObjectNode,
    StrBundleNode,
    SweepNode,
    VarNode,
)


class Unparser(NodeVisitor):
    """`NodeVisitor` for the `unparse` operation."""

    def visit_dict(self, node: DictNode) -> Dict:
        data = {}
        for k, v in node.nodes.items():
            data[k.accept(self)] = v.accept(self)
        return data

    def visit_list(self, node: ListNode) -> List:
        data = []
        for x in node.nodes:
            data.append(x.accept(self))
        return data

    def visit_object(self, node: ObjectNode) -> Any:
        return node.data

    def visit_str_bundle(self, node: StrBundleNode) -> str:
        return "".join(x.accept(self) for x in node.nodes)

    def visit_id(self, node: IdNode) -> str:
        return node.name

    def visit_sweep(self, node: SweepNode) -> str:
        body = self._unparse_as_args(*node.cases)
        return f"$sweep({body})"

    def visit_var(self, node: VarNode) -> str:
        default_str = ""
        if node.default is not None:
            default_str = f", default={self._unparse_as_arg(node.default)}"
        return f"$var({node.identifier.accept(self)}{default_str})"

    def visit_env(self, node: EnvNode) -> str:
        default_str = ""
        if node.default is not None:
            default_str = f", default={self._unparse_as_arg(node.default)}"
        return f"$env({node.identifier.accept(self)}{default_str})"

    def visit_import(self, node: ImportNode) -> str:
        return f'$import("{node.path.accept(self)}")'

    def _unparse_as_arg(self, node: Node) -> str:
        unparsed = node.accept(self)
        if isinstance(node, ObjectNode):
            if isinstance(unparsed, str):
                return f'"{unparsed}"'
            else:
                return str(unparsed)
        else:
            return str(unparsed)

    def _unparse_as_args(self, *nodes: Node) -> str:
        return ", ".join([self._unparse_as_arg(x) for x in nodes])


def unparse(node: Node) -> Any:
    """Visitor that undoes the parsing operation.

    If a parser transforms an object into an AST Node, the unparser transforms the AST
    Node back to an object that can be parsed into the same AST Node, as close as
    possible to the original object.

    Of course, since the parser discards some irrelevant information like unnecessary
    white spaces around tokens, the unparser cannot magically bring them back.
    For example::

        unparse(parse('$var( my_id  ,default= 10       '))

    results in::

        '$var(my_id, default=10)'

    Args:
        node (Node): The AST node to unparse.

    Returns:
        Any: The unparsed object.
    """
    unparser = Unparser()
    return node.accept(unparser)
