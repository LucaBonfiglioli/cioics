import yaml
from deepdiff import DeepDiff
from cioics.nodes import ObjectNode, StrBundleNode, SweepNode, VarNode

from cioics.parser import parse
from cioics.unparser import unparse


def test_parse_unparse(full_cfg):
    cfg = yaml.safe_load(open(full_cfg))
    parsed = parse(cfg)
    recfg = unparse(parsed)
    reparsed = parse(recfg)
    assert not DeepDiff(cfg, recfg)
    assert reparsed == parsed


class TestStrParser:
    def test_str_bundle(self):
        expr = "I am a string with $var(nested.variable.one) and $sweep(10, sasso.grosso, '30')"
        expected = StrBundleNode(
            ObjectNode("I am a string with "),
            VarNode("nested.variable.one"),
            ObjectNode(" and "),
            SweepNode(ObjectNode(10), VarNode("sasso.grosso"), ObjectNode("30")),
        )
        parsed = parse(expr)
        print(parsed)
        print(expected)
        assert parsed == expected
