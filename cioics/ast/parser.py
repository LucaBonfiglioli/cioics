import ast
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

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
    ObjectNode,
    StrBundleNode,
    SweepNode,
    VarNode,
)
from schema import Schema

DIRECTIVE_PREFIX = "$"
"""Prefix used at the start of all Choixe directives."""


@dataclass
class Token:
    name: str
    args: List[Node]
    kwargs: Dict[str, Node]


class Scanner:
    """Choixe Scanner of python str objects."""

    DIRECTIVE_RE = (
        rf"(?:\$[^\)\( \.\,\$]+\([^\(\)]*\))|(?:\$[^\)\( \.\,\$]+)|(?:[^\$]*)"
    )
    """Regex used to check if a string is a Choixe directive."""

    def _scan_argument(
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

    def _scan_directive(self, code: str) -> Token:
        py_ast = ast.parse(f"_{code}")  # Add "_" to avoid conflicts with python
        assert isinstance(py_ast, ast.Module)
        py_expr = py_ast.body[0].value

        if isinstance(py_expr, ast.Call):
            token_name = py_expr.func.id[1:]  # Remove the added "_"
            py_args = py_expr.args
            py_kwargs = py_expr.keywords
        elif isinstance(py_expr, ast.Name):
            token_name = py_expr.id[1:]
            py_args = []
            py_kwargs = {}
        else:
            raise SyntaxError(code)

        args = []
        for py_arg in py_args:
            args.append(self._scan_argument(py_arg))

        kwargs = {}
        for py_kwarg in py_kwargs:
            key, value = py_kwarg.arg, py_kwarg.value
            kwargs[key] = self._scan_argument(value)

        return Token(token_name, args, kwargs)

    def scan(self, data: str) -> List[Token]:
        """Transforms a string into a list of parsed tokens.

        Args:
            data (str): The string to parse.

        Returns:
            List[Token]: The list of parsed tokens.
        """
        res = []
        tokens = re.findall(self.DIRECTIVE_RE, data)
        for token in tokens:
            if len(token) == 0:
                continue
            if token.startswith(DIRECTIVE_PREFIX):
                token = self._scan_directive(token[len(DIRECTIVE_PREFIX) :])
            else:
                token = Token("str", [token], {})
            res.append(token)

        return res


class Parser:
    """Choixe parser for all kind of python objects."""

    def __init__(self) -> None:
        self._scanner = Scanner()
        self._type_map = {
            dict: self._parse_dict,
            list: self._parse_list,
            tuple: self._parse_list,
            str: self._parse_str,
        }

        self._dict_schemas = {
            Schema(
                {self._token_schema("call"): str, self._token_schema("args"): dict}
            ): self._parse_instance,
            Schema({self._token_schema("for"): object}): self._parse_for,
        }

        self._directive_map = {
            "var": VarNode,
            "import": ImportNode,
            "sweep": SweepNode,
            "str": ObjectNode,
            "index": IndexNode,
            "item": ItemNode,
        }

    def _token_schema(self, name: str) -> Schema:
        return Schema(lambda x: self._scanner.scan(x)[0].name == name)

    def _key_value_pairs_by_token_name(
        self, data: Dict[str, Any]
    ) -> Dict[str, Tuple[Token, Any]]:
        res = {}
        for k, v in data.items():
            token = self._scanner.scan(k)[0]
            res[token.name] = (token, v)
        return res

    def _parse_instance(self, data: dict) -> InstanceNode:
        pairs = self._key_value_pairs_by_token_name(data)
        symbol = ObjectNode(pairs["call"][1])
        args = self.parse(pairs["args"][1])
        return InstanceNode(symbol, args)

    def _parse_for(self, data: dict) -> ForNode:
        pairs = self._key_value_pairs_by_token_name(data)
        loop, body = pairs["for"]
        return ForNode(*loop.args, **loop.kwargs, body=self.parse(body))

    def _parse_dict(self, data: dict) -> DictNode:
        for schema, fn in self._dict_schemas.items():
            if schema.is_valid(data):
                return fn(data)

        return DictNode({self._parse_str(k): self.parse(v) for k, v in data.items()})

    def _parse_list(self, data: list) -> ListNode:
        return ListNode(*[self.parse(x) for x in data])

    def _parse_str(self, data: str) -> Node:
        nodes = []
        for token in self._scanner.scan(data):
            if token.name not in self._directive_map:
                raise NotImplementedError(token.name)
            node = self._directive_map[token.name](*token.args, **token.kwargs)
            nodes.append(node)

        if len(nodes) == 1:
            return nodes[0]
        else:
            return StrBundleNode(*nodes)

    def parse(self, data: Any) -> Node:
        """Recursively transforms an object into a visitable AST node.

        Args:
            data (Any): The object to parse.

        Returns:
            Node: The parsed Choixe AST node.
        """
        fn = ObjectNode
        for type_, parse_fn in self._type_map.items():
            if isinstance(data, type_):
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
