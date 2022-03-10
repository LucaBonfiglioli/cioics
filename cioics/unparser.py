from typing import Any, Dict, List

from cioics.nodes import (
    DictNode,
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
    def unparse(self, node: Node) -> Any:
        return node.accept(self)

    def visit_dict_node(self, node: DictNode) -> Dict:
        data = {}
        for k, v in node.nodes.items():
            data[self.unparse(k)] = self.unparse(v)
        return data

    def visit_list_node(self, node: ListNode) -> List:
        data = []
        for x in node.nodes:
            data.append(self.unparse(x))
        return data

    def visit_object_node(self, node: ObjectNode) -> Any:
        return node.data

    def visit_str_bundle_node(self, node: StrBundleNode) -> str:
        return "".join(self.unparse(x) for x in node.nodes)

    def visit_id_node(self, node: IdNode) -> str:
        return node.name

    def visit_sweep_node(self, node: SweepNode) -> str:
        body = self._unparse_as_args(*node.cases)
        return f"$sweep({body})"

    def visit_var_node(self, node: VarNode) -> str:
        return f"$var({self.unparse(node.identifier)})"

    def visit_import_node(self, node: ImportNode) -> str:
        return f'$import("{self.unparse(node.path)}")'

    def _unparse_as_arg(self, node: Node) -> str:
        unparsed = self.unparse(node)
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
    unparser = Unparser()
    return unparser.unparse(node)
