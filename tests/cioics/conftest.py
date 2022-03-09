import pytest
from pathlib import Path


@pytest.fixture
def sample_data():
    return Path(__file__).parent.parent / "sample_data"


@pytest.fixture
def full_cfg(sample_data):
    return sample_data / "full_cfg.yml"
