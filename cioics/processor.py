from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pydash as py_

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
from choixe.configurations import XConfig  # TODO: import xconfig in cioics


@dataclass
class ProcessorContext:
    data: Dict[str, Any]
    sweep_state: Dict[str, int]


class Processor(NodeVisitor):
    def __init__(self, context: ProcessorContext) -> None:
        super().__init__()
        self._context = context
        self._data = None

    def visit_dict_node(self, node: DictNode) -> None:
        self._data = {}
        for k, v in node.nodes.items():
            self._data[process(k, self._context)] = process(v, self._context)

    def visit_list_node(self, node: ListNode) -> None:
        self._data = []
        for x in node.nodes:
            self._data.append(process(x, self._context))

    def visit_object_node(self, node: ObjectNode) -> None:
        self._data = node.data

    def visit_str_bundle_node(self, node: StrBundleNode) -> None:
        self._data = "".join(process(x, self._context) for x in node.nodes)

    def visit_id_node(self, node: IdNode) -> None:
        self._data = py_.get(self._context.data, node.name)

    def visit_var_node(self, node: VarNode) -> None:
        self._data = py_.get(self._context.data, node.identifier.name, node.default)

    def visit_import_node(self, node: ImportNode) -> None:
        path = process(node.path, self._context)
        path = Path(path)
        subdata = XConfig(path).to_dict()
        parsed = parse(subdata)
        self._data = process(parsed, self._context)

    def visit_sweep_node(self, node: SweepNode) -> None:
        pass

    @property
    def data(self) -> Any:
        return self._data


def process(node: Node, context: ProcessorContext) -> Any:
    processor = Processor(context)
    node.accept(processor)
    return processor.data
