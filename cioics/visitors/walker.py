from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple, Union

from cioics.ast.nodes import DictNode, ListNode, Node
from cioics.visitors.unparser import Unparser


@dataclass
class Entry:
    key: Sequence[Union[str, int]]
    value: Any

    def prepend(self, key) -> Entry:
        return Entry((key, *self.key), self.value)


@dataclass
class Chunk:
    entries: Sequence[Entry] = tuple()

    def prepend(self, key: Union[int, str]) -> Chunk:
        return Chunk((x.prepend(key) for x in self.entries))

    def __add__(self, other: Chunk) -> Chunk:
        return Chunk(self.entries + other.entries)


# 🏜️🤠🌵
class Walker(Unparser):
    def visit_dict_node(self, node: DictNode) -> Chunk:
        chunk = Chunk()
        for k, v in node.nodes.items():
            key = k.accept(self)
            value = v.accept(self)
            assert isinstance(key, str), "Only string keys are allowed in dict walk"

            if not isinstance(value, Chunk):
                value = Chunk((Entry((key,), value),))

            chunk += value.prepend(key)

        return chunk

    def visit_list_node(self, node: ListNode) -> Chunk:
        chunk = Chunk()
        for i, x in enumerate(node.nodes):
            value = x.accept(self)

            if not isinstance(value, Chunk):
                value = Chunk((Entry((i,), value),))

            chunk += value.prepend(i)

        return chunk


def walk(node: Node) -> List[Tuple[List[Union[str, int]], Any]]:
    chunk: Chunk = node.accept(Walker())
    if not isinstance(chunk, Chunk):
        return [(tuple(), chunk)]
    return [(list(x.key), x.value) for x in chunk.entries]
