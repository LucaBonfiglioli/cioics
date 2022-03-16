from __future__ import annotations


class MyClass:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __repr__(self) -> str:
        return f"MyClass({self.a}, {self.b})"
