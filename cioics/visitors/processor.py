import os
from copy import deepcopy
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Optional

import pydash as py_
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
from cioics.ast.parser import parse
from cioics.utils.io import load
from cioics.visitors.unparser import unparse


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
                data[i] += branches[i // N]
        return data

    def visit_id(self, node: IdNode) -> List[Any]:
        return [py_.get(self._context, node.name)]

    def visit_var(self, node: VarNode) -> List[Any]:
        branches = [node.default]
        if node.default is not None:
            branches = node.default.accept(self)
        return [py_.get(self._context, node.identifier.name, x) for x in branches]

    def visit_env(self, node: EnvNode) -> List[Any]:
        branches = [node.default]
        if node.default is not None:
            branches = node.default.accept(self)
        return [os.getenv(node.identifier.name, default=x) for x in branches]

    def visit_import(self, node: ImportNode) -> List[Any]:
        branches = node.path.accept(self)
        data = []
        for branch in branches:
            path = Path(branch)
            if not path.is_absolute():
                path = self._cwd / path

            subdata = load(path)
            parsed = parse(subdata)
            data.extend(parsed.accept(self))
        return data

    def visit_sweep(self, node: SweepNode) -> List[Any]:
        if self._allow_branching:
            cases = []
            for x in node.cases:
                cases.extend(x.accept(self))
            return cases
        else:
            return [unparse(node)]


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
