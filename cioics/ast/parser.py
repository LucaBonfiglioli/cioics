import ast
import re
from typing import Any, Union

from cioics.ast.nodes import (
    EnvNode,
    ImportNode,
    Node,
    DictNode,
    ListNode,
    ObjectNode,
    IdNode,
    StrBundleNode,
    SweepNode,
    VarNode,
)


class DictParser:
    @classmethod
    def parse_dict(cls, data: dict) -> DictNode:
        return DictNode(
            {StrParser.parse_str(k): Parser.parse(v) for k, v in data.items()}
        )


class ListParser:
    @classmethod
    def parse_list(cls, data: list) -> ListNode:
        return ListNode(*[Parser.parse(x) for x in data])


class StrParser:
    DIRECTIVE_PREFIX = "$"
    DIRECTIVE_RE = rf"(?:\{DIRECTIVE_PREFIX}[^\)]+\))|(?:[^\$]*)"

    _fn_map = {
        "var": VarNode,
        "env": EnvNode,
        "import": ImportNode,
        "sweep": SweepNode,
    }

    @classmethod
    def _parse_argument(
        cls, py_arg: Union[ast.Constant, ast.Attribute, ast.Name]
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

    @classmethod
    def _parse_directive(cls, code: str) -> Node:
        py_ast = ast.parse(f"_{code}")  # Add "_" to avoid conflicts with python
        assert isinstance(py_ast, ast.Module)
        py_call = py_ast.body[0].value
        assert isinstance(py_call, ast.Call)
        directive_name = py_call.func.id[1:]  # Remove the added "_"
        py_args = py_call.args
        py_kwargs = py_call.keywords

        args = []
        for py_arg in py_args:
            args.append(cls._parse_argument(py_arg))

        kwargs = {}
        for py_kwarg in py_kwargs:
            key, value = py_kwarg.arg, py_kwarg.value
            kwargs[key] = cls._parse_argument(value)

        if directive_name not in cls._fn_map:
            raise NotImplementedError(directive_name)

        return cls._fn_map[directive_name](*args, **kwargs)

    @classmethod
    def parse_str(cls, data: str) -> Node:
        nodes = []
        tokens = re.findall(cls.DIRECTIVE_RE, data)
        for token in tokens:
            if len(token) == 0:
                continue
            if token.startswith(cls.DIRECTIVE_PREFIX):
                node = cls._parse_directive(token[len(cls.DIRECTIVE_PREFIX) :])
            else:
                node = ObjectNode(token)
            nodes.append(node)

        if len(nodes) > 1:
            return StrBundleNode(*nodes)
        else:
            return nodes[0]


class Parser:
    _fn_map = {
        dict: DictParser.parse_dict,
        list: ListParser.parse_list,
        tuple: ListParser.parse_list,
        str: StrParser.parse_str,
    }

    @classmethod
    def parse(cls, data: Any) -> Node:
        fn = ObjectNode
        for k, v in cls._fn_map.items():
            if isinstance(data, k):
                fn = v
                break
        return fn(data)


def parse(data: Any) -> Node:
    return Parser.parse(data)
