from cioics.parser import parse
from cioics.processor import Processor


class TestProcessor:
    def test_sweep(self):
        data = {
            "a": "$sweep(1096, 20.0, '40', nested.variable)",
            "b": {
                "a": "$sweep('hello')",
                "b": "$sweep('hello', 'world')",
                "c": "$sweep('hello', 'world')",
            },
        }
        parsed = parse(data)
        processor = Processor({"nested": {"variable": 3215}})

        for _ in range(16):
            processed = parsed.accept(processor)
            processor.advance_sweep_state()
            print(processed)
        assert False
