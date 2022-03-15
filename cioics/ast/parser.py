import ast
import re
from typing import Any, Union

from cioics.ast.nodes import (
    EnvNode,
    ImportNode,
    InstanceNode,
    Node,
    DictNode,
    ListNode,
    ObjectNode,
    IdNode,
    StrBundleNode,
    SweepNode,
    VarNode,
)
from schema import Schema

DIRECTIVE_PREFIX = "$"
"""Prefix used at the start of all Choixe directives."""


class StrParser:
    """Parser of python str objects."""

    DIRECTIVE_RE = rf"(?:\{DIRECTIVE_PREFIX}[^\)]+\))|(?:[^\$]*)"
    """Regex used to check if a string is a Choixe directive."""

    _fn_map = {
        "var": VarNode,
        "env": EnvNode,
        "import": ImportNode,
        "sweep": SweepNode,
    }

    def _parse_argument(
        self, py_arg: Union[ast.Constant, ast.Attribute, ast.Name]
    ) -> Node:
        if isinstance(py_arg, ast.Constant):
            return ObjectNode(py_arg.value)
        elif isinstance(py_arg, ast.Attribute):
            name = ast.unparse(py_arg)
            return IdNode(name)
        elif isinstance(py_arg, ast.Name):
            return IdNode(py_arg.id)
        else:
            raise NotImplementedError(py_arg.__class__)

    def _parse_directive(self, code: str) -> Node:
        py_ast = ast.parse(f"_{code}")  # Add "_" to avoid conflicts with python
        assert isinstance(py_ast, ast.Module)
        py_call = py_ast.body[0].value
        assert isinstance(py_call, ast.Call)
        directive_name = py_call.func.id[1:]  # Remove the added "_"
        py_args = py_call.args
        py_kwargs = py_call.keywords

        args = []
        for py_arg in py_args:
            args.append(self._parse_argument(py_arg))

        kwargs = {}
        for py_kwarg in py_kwargs:
            key, value = py_kwarg.arg, py_kwarg.value
            kwargs[key] = self._parse_argument(value)

        if directive_name not in self._fn_map:
            raise NotImplementedError(directive_name)

        return self._fn_map[directive_name](*args, **kwargs)

    def parse_str(self, data: str) -> Node:
        """Transforms a string into a `Node`.

        Args:
            data (str): The string to parse.

        Returns:
            Node: The parsed Choixe AST node.
        """
        nodes = []
        tokens = re.findall(self.DIRECTIVE_RE, data)
        for token in tokens:
            if len(token) == 0:
                continue
            if token.startswith(DIRECTIVE_PREFIX):
                node = self._parse_directive(token[len(DIRECTIVE_PREFIX) :])
            else:
                node = ObjectNode(token)
            nodes.append(node)

        if len(nodes) > 1:
            return StrBundleNode(*nodes)
        else:
            return nodes[0]


class Parser:
    """Choixe parser for all kind of python objects."""

    def __init__(self) -> None:
        self._string_parser = StrParser()
        self._fn_map = [
            (
                {f"{DIRECTIVE_PREFIX}call": str, f"{DIRECTIVE_PREFIX}args": dict},
                self._parse_instance,
            ),
            (dict, self._parse_dict),
            (list, self._parse_list),
            (tuple, self._parse_list),
            (str, self._string_parser.parse_str),
        ]

    def _parse_instance(self, data: dict) -> InstanceNode:
        classpath = ObjectNode(data[f"{DIRECTIVE_PREFIX}call"])
        args = self.parse(data[f"{DIRECTIVE_PREFIX}args"])
        return InstanceNode(classpath, args)

    def _parse_dict(self, data: dict) -> DictNode:
        return DictNode(
            {self._string_parser.parse_str(k): self.parse(v) for k, v in data.items()}
        )

    def _parse_list(self, data: list) -> ListNode:
        return ListNode(*[self.parse(x) for x in data])

    def parse(self, data: Any) -> Node:
        """Recursively transforms an object into a visitable AST node.

        Args:
            data (Any): The object to parse.

        Returns:
            Node: The parsed Choixe AST node.
        """
        fn = ObjectNode
        for data_schema, parse_fn in self._fn_map:
            if Schema(data_schema).is_valid(data):
                fn = parse_fn
                break
        return fn(data)


def parse(data: Any) -> Node:
    """Recursively transforms an object into a visitable AST node.

    Args:
        data (Any): The object to parse.

    Returns:
        Node: The parsed Choixe AST node.
    """
    return Parser().parse(data)
