from copy import deepcopy
from pathlib import Path

from deepdiff import DeepDiff
from schema import Or, Schema, Use

from cioics.ast.parser import parse
from cioics.utils.io import load
from cioics.visitors import process, walk
from cioics.visitors.unparser import unparse
from cioics.xconfig import XConfig


class TestXConfig:
    def _copy_test(self, cfg: XConfig):
        cfg_copy = cfg.copy()
        assert not DeepDiff(cfg_copy.to_dict(), cfg.to_dict())
        assert cfg_copy.get_schema() == cfg.get_schema()
        assert cfg_copy.get_filename() == cfg.get_filename()

    def test_from_file(self, plain_cfg: Path):
        cfg = XConfig(filename=plain_cfg)
        assert not DeepDiff(cfg.to_dict(), load(plain_cfg))
        assert cfg.get_filename() == plain_cfg
        self._copy_test(cfg)

    def test_from_dict(self, plain_cfg: Path):
        data = load(plain_cfg)
        cfg = XConfig(plain_dict=data)
        assert not DeepDiff(cfg.to_dict(), data)
        assert cfg.get_filename() is None
        self._copy_test(cfg)

    def test_from_nothing(self):
        cfg = XConfig()
        assert not DeepDiff(cfg.to_dict(), {})
        assert cfg.get_filename() is None
        self._copy_test(cfg)

    def test_file_io(self, tmp_path: Path, plain_cfg: Path):
        cfg = XConfig(plain_cfg)
        save_path = tmp_path / "config.yml"
        cfg.save_to(save_path)
        recfg = XConfig(filename=save_path)

        assert recfg.get_filename() == save_path
        assert not DeepDiff(recfg.to_dict(), cfg.to_dict())

    def test_with_schema(self, plain_cfg: Path):
        cfg = XConfig(plain_cfg)
        assert cfg.is_valid()  # No schema: always valid

        schema = Schema(
            {"alice": int, "bob": int, "charlie": [Or(str, {str: Use(int)})]}
        )
        cfg.set_schema(schema)
        assert cfg.get_schema() == schema
        assert cfg.is_valid()
        cfg.validate()
        expected = schema.validate(load(plain_cfg))
        assert not DeepDiff(cfg.to_dict(), expected)

    def test_deep_keys(self, plain_cfg: Path):
        cfg = XConfig(plain_cfg)
        assert cfg.deep_get("charlie.2.alpha") == 10.0
        assert cfg.deep_get(["charlie", 2, "beta"]) == 20.0
        assert cfg.deep_get("bob.alpha", default="hello") == "hello"

        cfg.deep_set("charlie.2.alpha", 40, only_valid_keys=False)
        assert cfg.deep_get("charlie.2.alpha") == 40

        cfg.deep_set("charlie.2.alpha", 50, only_valid_keys=True)
        assert cfg.deep_get("charlie.2.alpha") == 50

        cfg.deep_set("charlie.3.foo.bar", [10, 20, 30], only_valid_keys=False)
        assert cfg.deep_get("charlie.3") == {"foo": {"bar": [10, 20, 30]}}

        cfg.deep_set("charlie.4.foo.bar", [10, 20, 30], only_valid_keys=True)
        assert cfg.deep_get("charlie.4") is None

    def test_deep_update(self):
        data = {
            "a": {"b": 10},
            "b": [0, 2, 1.02],
            "c": {"a": "b", "b": [{"a": 1, "b": 2}, "a"]},
        }
        other = {"c": {"b": [{"a": 2}], "e": {"a": 18, "b": "a"}}}
        cfg = XConfig(plain_dict=data)
        cfg.deep_update(other)
        expected = deepcopy(data)
        expected["c"]["b"][0]["a"] = 2
        assert not DeepDiff(cfg.to_dict(), expected)

    def test_full_merge(self):
        data = {
            "a": {"b": 10},
            "b": [0, 2, 1.02],
            "c": {"a": "b", "b": [{"a": 1, "b": 2}, "a"]},
        }
        other = {"c": {"b": [{"a": 2}], "e": {"a": 18, "b": "a"}}}
        cfg = XConfig(plain_dict=data)
        cfg.deep_update(other, full_merge=True)
        expected = {
            "a": {"b": 10},
            "b": [0, 2, 1.02],
            "c": {"a": "b", "b": [{"a": 2, "b": 2}, "a"], "e": {"a": 18, "b": "a"}},
        }
        assert not DeepDiff(cfg.to_dict(), expected)

    def test_walk(self, plain_cfg: Path):
        cfg = XConfig(plain_cfg)
        assert not DeepDiff(cfg.walk(), walk(parse(load(plain_cfg))))

    def test_process(self, plain_cfg: Path):
        cfg = XConfig(plain_cfg)
        processed = cfg.process().to_dict()
        processed_expected = process(parse(load(plain_cfg)), allow_branching=False)[0]
        assert not DeepDiff(processed, processed_expected)

    def test_process_all(self, plain_cfg: Path):
        cfg = XConfig(plain_cfg)
        processed = cfg.process_all()
        processed_expected = process(parse(load(plain_cfg)), allow_branching=True)
        for a, b in zip(processed, processed_expected):
            assert not DeepDiff(a.to_dict(), b)
