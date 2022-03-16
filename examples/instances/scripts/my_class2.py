from __future__ import annotations

from my_class import MyClass


class MyClass2(MyClass):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __repr__(self) -> str:
        return f"MyClass2({self.a}, {self.b})"
