from cioics.nodes import IdNode, ObjectNode, StrBundleNode, SweepNode, VarNode
from cioics.parser import parse


class TestParser:
    def test_str_bundle(self):
        expr = "I am a string with $var(nested.variable.one) and $sweep(10, sasso.grosso, '30')"
        expected = StrBundleNode(
            ObjectNode("I am a string with "),
            VarNode(IdNode("nested.variable.one")),
            ObjectNode(" and "),
            SweepNode(ObjectNode(10), IdNode("sasso.grosso"), ObjectNode("30")),
        )
        parsed = parse(expr)
        assert parsed == expected
