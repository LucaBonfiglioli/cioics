from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pydash as py_
from choixe.configurations import XConfig  # TODO: import xconfig in cioics

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
from cioics.parser import parse
from cioics.unparser import unparse


@dataclass
class ProcessorContext:
    data: Dict[str, Any]
    sweep_state: Dict[str, int]


class Processor(NodeVisitor):
    def __init__(self, context: ProcessorContext) -> None:
        super().__init__()
        self._context = context

    def process(self, node: Node) -> Any:
        return node.accept(self)

    def visit_dict_node(self, node: DictNode) -> None:
        data = {}
        for k, v in node.nodes.items():
            data[self.process(k)] = self.process(v)
        return data

    def visit_list_node(self, node: ListNode) -> None:
        data = []
        for x in node.nodes:
            data.append(self.process(x))
        return data

    def visit_object_node(self, node: ObjectNode) -> None:
        return node.data

    def visit_str_bundle_node(self, node: StrBundleNode) -> None:
        return "".join(self.process(x) for x in node.nodes)

    def visit_id_node(self, node: IdNode) -> None:
        return py_.get(self._context.data, node.name)

    def visit_var_node(self, node: VarNode) -> None:
        return py_.get(self._context.data, node.identifier.name, node.default)

    def visit_import_node(self, node: ImportNode) -> None:
        path = self.process(node.path)
        path = Path(path)
        subdata = XConfig(path).to_dict()
        parsed = parse(subdata)
        return self.process(parsed)

    def visit_sweep_node(self, node: SweepNode) -> None:
        return unparse(node)

    @property
    def data(self) -> Any:
        return self._data
