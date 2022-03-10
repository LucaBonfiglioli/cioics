import os
from copy import deepcopy
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pydash as py_
from cioics.ast.nodes import (
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
from cioics.ast.parser import parse
from cioics.utils.io import load


class Processor(NodeVisitor):
    def __init__(
        self, context: Optional[Dict[str, Any]] = None, cwd: Optional[Path] = None
    ) -> None:
        super().__init__()
        self._context = context if context is not None else {}
        self._cwd = cwd if cwd is not None else Path(os.getcwd())

    def visit_dict_node(self, node: DictNode) -> List[Dict]:
        data = [{}]
        for k, v in node.nodes.items():
            branches = list(product(k.accept(self), v.accept(self)))
            new_data = []
            for _ in range(len(branches)):
                new_data.extend(deepcopy(data))
            for i, d in enumerate(new_data):
                d[branches[i // len(data)][0]] = branches[i // len(data)][1]
            data = new_data
        return data

    def visit_list_node(self, node: ListNode) -> List[List]:
        data = [[]]
        for x in node.nodes:
            branches = x.accept(self)
            new_data = []
            for _ in range(len(branches)):
                new_data.extend(deepcopy(data))
            for i, d in enumerate(new_data):
                d.append(branches[i // len(data)])
            data = new_data
        return data

    def visit_object_node(self, node: ObjectNode) -> List[Any]:
        return [node.data]

    def visit_str_bundle_node(self, node: StrBundleNode) -> List[str]:
        data = [""]
        for x in node.nodes:
            branches = x.accept(self)
            N = len(data)
            data *= len(branches)
            for i in range(len(data)):
                data[i] += branches[i // N]
        return data

    def visit_id_node(self, node: IdNode) -> List[Any]:
        return [py_.get(self._context, node.name)]

    def visit_var_node(self, node: VarNode) -> List[Any]:
        return [py_.get(self._context, node.identifier.name, node.default)]

    def visit_import_node(self, node: ImportNode) -> List[Any]:
        path = node.path.accept(self)

        path = Path(path)
        if not path.is_absolute():
            path = self._cwd / path

        subdata = load(path)
        parsed = parse(subdata)
        return [parsed.accept(self)]

    def visit_sweep_node(self, node: SweepNode) -> List[Any]:
        cases = []
        for x in node.cases:
            cases.extend(x.accept(self))
        return cases


def process(
    self,
    node: Node,
    context: Optional[Dict[str, Any]] = None,
    cwd: Optional[Path] = None,
) -> Sequence[Any]:
    processor = Processor(context=context, cwd=cwd)
    return node.accept(processor)
