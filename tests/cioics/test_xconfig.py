from pathlib import Path

from deepdiff import DeepDiff

from cioics.utils.io import load
from cioics.xconfig import XConfig


class TestXConfig:
    def test_plain(self, plain_cfg: Path):
        cfg = XConfig(plain_cfg)
        print(cfg)
        assert not DeepDiff(cfg.to_dict(), load(plain_cfg))
