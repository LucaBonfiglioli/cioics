import os
from copy import deepcopy
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional

import pydash as py_
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
from cioics.ast.parser import parse
from cioics.utils.imports import import_symbol
from cioics.utils.io import load
from cioics.visitors.unparser import unparse


@dataclass
class LoopInfo:
    index: int
    item: Any


class Processor(NodeVisitor):
    """`NodeVisitor` that implements the processing logic of Choixe."""

    def __init__(
        self,
        context: Optional[Dict[str, Any]] = None,
        cwd: Optional[Path] = None,
        allow_branching: bool = True,
    ) -> None:
        """Constructor for `Processor`

        Args:
            context (Optional[Dict[str, Any]], optional): A data structure containing
            the values that will replace the variable nodes. Defaults to None.
            cwd (Optional[Path], optional): current working directory used for relative
            imports. If set to None, the `os.getcwd()` will be used. Defaults to None.
            allow_branching (bool, optional): Set to False to disable processing on
            branching nodes, like sweeps. All branching nodes will be simply unparsed.
            Defaults to True.
        """
        super().__init__()
        self._context = context if context is not None else {}
        self._cwd = cwd if cwd is not None else Path(os.getcwd())
        self._allow_branching = allow_branching

        self._loop_data: Dict[str, LoopInfo] = {}

    def visit_dict(self, node: DictNode) -> List[Dict]:
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

    def visit_list(self, node: ListNode) -> List[List]:
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

    def visit_object(self, node: ObjectNode) -> List[Any]:
        return [node.data]

    def visit_str_bundle(self, node: StrBundleNode) -> List[str]:
        data = [""]
        for x in node.nodes:
            branches = x.accept(self)
            N = len(data)
            data *= len(branches)
            for i in range(len(data)):
                data[i] += str(branches[i // N])
        return data

    def visit_id(self, node: IdNode) -> List[Any]:
        return [py_.get(self._context, node.name)]

    def visit_var(self, node: VarNode) -> List[Any]:
        default = None
        if node.default is not None:
            default = node.default.accept(self)[0]

        if node.env is not None and node.env.accept(self)[0]:
            default = os.getenv(node.identifier.name, default=default)

        return [py_.get(self._context, node.identifier.name, default)]

    def visit_import(self, node: ImportNode) -> List[Any]:
        path = Path(node.path.accept(self)[0])
        if not path.is_absolute():
            path = self._cwd / path

        subdata = load(path)
        parsed = parse(subdata)

        old_cwd = self._cwd
        self._cwd = path.parent
        nested = parsed.accept(self)
        self._cwd = old_cwd

        return nested

    def visit_sweep(self, node: SweepNode) -> List[Any]:
        if self._allow_branching:
            cases = []
            for x in node.cases:
                cases.extend(x.accept(self))
            return cases
        else:
            return [unparse(node)]

    def visit_instance(self, node: InstanceNode) -> List[Any]:
        branches = list(product(node.symbol.accept(self), node.args.accept(self)))
        data = []
        for symbol, args in branches:
            fn = import_symbol(symbol, cwd=self._cwd)
            data.append(fn(**args))
        return data

    def visit_for(self, node: ForNode) -> List[Any]:
        iterable = node.iterable.accept(self)[0]
        id_ = node.identifier.name

        branches = []
        for i, x in enumerate(iterable):
            self._loop_data[id_] = LoopInfo(i, x)
            branches.append(node.body.accept(self))

        branches = list(product(*branches))

        for i, branch in enumerate(branches):
            if isinstance(node.body, DictNode):
                res = {}
                [res.update(item) for item in branch]
            elif isinstance(node.body, ListNode):
                res = []
                [res.extend(item) for item in branch]
            else:
                res = "".join([str(item) for item in branch])
            branches[i] = res

        return branches

    def visit_index(self, node: IndexNode) -> List[Any]:
        return [self._loop_data[node.identifier.name].index]

    def visit_item(self, node: ItemNode) -> List[Any]:
        sep = "."
        loop_id, _, key = node.identifier.name.partition(sep)
        return [py_.get(self._loop_data[loop_id].item, f"{sep}{key}")]


def process(
    node: Node,
    context: Optional[Dict[str, Any]] = None,
    cwd: Optional[Path] = None,
    allow_branching: bool = True,
) -> Any:
    """Processes a Choixe AST node into a list of all possible outcomes.

    Args:
        node (Node): The AST node to process.
        context (Optional[Dict[str, Any]], optional): A data structure containing
        the values that will replace the variable nodes. Defaults to None.
        cwd (Optional[Path], optional): current working directory used for relative
        imports. If set to None, the `os.getcwd()` will be used. Defaults to None.
        allow_branching (bool, optional): Set to False to disable processing on
        branching nodes, like sweeps. All branching nodes will be simply unparsed.
        Defaults to True.

    Returns:
        Any: The list of all possible outcomes. If branching is disabled, the list will
        have length 1.
    """
    processor = Processor(context=context, cwd=cwd, allow_branching=allow_branching)
    return node.accept(processor)
