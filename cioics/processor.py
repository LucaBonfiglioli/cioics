from pathlib import Path
from typing import Any, Dict, List, Tuple

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


class Processor(NodeVisitor):
    def __init__(self, context: Dict[str, Any]) -> None:
        super().__init__()
        self._context = context
        self._sweep_state: List[Tuple[SweepNode, int]] = []

    def advance_sweep_state(self) -> None:
        for i, (sweep, counter) in enumerate(self._sweep_state):
            counter = (counter + 1) % len(sweep.cases)
            self._sweep_state[i] = (sweep, counter)
            if counter != 0:
                break

    def _get_sweep_case(self, sweep: SweepNode) -> Node:
        for x, counter in self._sweep_state:
            if x is sweep:
                return x.cases[counter]
        self._sweep_state.append((sweep, 0))
        return sweep.cases[0]

    def visit_dict_node(self, node: DictNode) -> None:
        data = {}
        for k, v in node.nodes.items():
            data[k.accept(self)] = v.accept(self)
        return data

    def visit_list_node(self, node: ListNode) -> None:
        data = []
        for x in node.nodes:
            data.append(x.accept(self))
        return data

    def visit_object_node(self, node: ObjectNode) -> None:
        return node.data

    def visit_str_bundle_node(self, node: StrBundleNode) -> None:
        return "".join(x.accept(self) for x in node.nodes)

    def visit_id_node(self, node: IdNode) -> None:
        return py_.get(self._context, node.name)

    def visit_var_node(self, node: VarNode) -> None:
        return py_.get(self._context, node.identifier.name, node.default)

    def visit_import_node(self, node: ImportNode) -> None:
        path = node.path.accept(self)
        path = Path(path)
        subdata = XConfig(path).to_dict()
        parsed = parse(subdata)
        return parsed.accept(self)

    def visit_sweep_node(self, node: SweepNode) -> str:
        subnode = self._get_sweep_case(node)
        return subnode.accept(self)
