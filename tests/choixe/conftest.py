import pytest
from pathlib import Path


@pytest.fixture
def sample_data():
    return Path(__file__).parent.parent / "sample_data"


@pytest.fixture
def plain_cfg(sample_data):
    return sample_data / "plain_cfg.yml"
