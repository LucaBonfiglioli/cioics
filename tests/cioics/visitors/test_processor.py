from deepdiff import DeepDiff

from cioics.ast.parser import parse
from cioics.visitors.processor import Processor


class TestProcessor:
    _processor = Processor({"nested": {"variable": 3215}})

    def _expectation_test(self, data, expected) -> None:
        parsed = parse(data)
        res = parsed.accept(self._processor)
        [print(x) for x in res]
        assert not DeepDiff(res, expected)

    def test_sweep_base(self):
        data = {
            "a": "$sweep(1096, 20.0, '40', nested.variable)",
            "b": {
                "a": "$sweep('hello')",
                "b": "$sweep('hello', 'world')",
                "c": "$sweep('hello', 'world')",
                "d": 10,
            },
        }
        expected = [
            {"a": 1096, "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": 3215, "b": {"a": "hello", "b": "hello", "c": "hello", "d": 10}},
            {"a": 1096, "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": 3215, "b": {"a": "hello", "b": "world", "c": "hello", "d": 10}},
            {"a": 1096, "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": 3215, "b": {"a": "hello", "b": "hello", "c": "world", "d": 10}},
            {"a": 1096, "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
            {"a": 20.0, "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
            {"a": "40", "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
            {"a": 3215, "b": {"a": "hello", "b": "world", "c": "world", "d": 10}},
        ]
        self._expectation_test(data, expected)

    def test_sweep_lists(self):
        data = ["$sweep(10, 20)", {"a": ["$sweep(30, 40)"]}]
        expected = [
            [10, {"a": [30]}],
            [20, {"a": [30]}],
            [10, {"a": [40]}],
            [20, {"a": [40]}],
        ]
        self._expectation_test(data, expected)

    def test_sweep_str_bundle(self):
        data = {"a": "I am a $sweep('red', 'blue') $sweep('sheep', 'cow')"}
        expected = [
            {"a": "I am a red sheep"},
            {"a": "I am a blue sheep"},
            {"a": "I am a red cow"},
            {"a": "I am a blue cow"},
        ]
        self._expectation_test(data, expected)

    def test_sweep_multikey(self):
        data = {
            "$sweep('foo', 'bar')": "$sweep('alice', 'bob')",
            "$sweep('alpha', 'beta')": "$sweep(10, 20)",
        }
        expected = [
            {"foo": "alice", "alpha": 10},
            {"foo": "bob", "alpha": 10},
            {"bar": "alice", "alpha": 10},
            {"bar": "bob", "alpha": 10},
            {"foo": "alice", "alpha": 20},
            {"foo": "bob", "alpha": 20},
            {"bar": "alice", "alpha": 20},
            {"bar": "bob", "alpha": 20},
            {"foo": "alice", "beta": 10},
            {"foo": "bob", "beta": 10},
            {"bar": "alice", "beta": 10},
            {"bar": "bob", "beta": 10},
            {"foo": "alice", "beta": 20},
            {"foo": "bob", "beta": 20},
            {"bar": "alice", "beta": 20},
            {"bar": "bob", "beta": 20},
        ]
        self._expectation_test(data, expected)
