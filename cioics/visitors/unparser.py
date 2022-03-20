from typing import Any, Dict, List

from cioics.ast.nodes import (
    DictNode,
    ForNode,
    IdNode,
    ImportNode,
    IndexNode,
    InstanceNode,
    ItemNode,
    ListNode,
    Node,
    NodeVisitor,
    ObjectNode,
    StrBundleNode,
    SweepNode,
    VarNode,
)
from cioics.ast.parser import DIRECTIVE_PREFIX


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
        return self._unparse_as_call("sweep", *node.cases)

    def visit_var(self, node: VarNode) -> str:
        kwargs = {}
        if node.default is not None:
            kwargs["default"] = node.default
        if node.env is not None:
            kwargs["env"] = node.env
        return self._unparse_as_call("var", node.identifier, **kwargs)

    def visit_import(self, node: ImportNode) -> str:
        return self._unparse_as_call("import", node.path)

    def visit_instance(self, node: InstanceNode) -> Dict[str, Any]:
        return {
            self._unparse_compact("call"): node.symbol.accept(self),
            self._unparse_compact("args"): node.args.accept(self),
        }

    def visit_for(self, node: ForNode) -> Any:
        key = self._unparse_as_call("for", node.iterable, node.identifier)
        value = node.body.accept(self)
        return {key: value}

    def visit_item(self, node: ItemNode) -> Any:
        return self._unparse_as_call("item", node.identifier)

    def visit_index(self, node: IndexNode) -> Any:
        return self._unparse_as_call("index", node.identifier)

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

    def _unparse_as_kwargs(self, **nodes: Node) -> str:
        return ", ".join([f"{k}={self._unparse_as_arg(v)}" for k, v in nodes.items()])

    def _unparse_compact(self, name: str) -> str:
        return f"{DIRECTIVE_PREFIX}{name}"

    def _unparse_as_call(self, name: str, *args: Node, **kwargs: Node) -> str:
        parts = []
        if len(args) > 0:
            parts.append(self._unparse_as_args(*args))
        if len(kwargs) > 0:
            parts.append(self._unparse_as_kwargs(**kwargs))
        return f"{self._unparse_compact(name)}({', '.join(parts)})"


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
