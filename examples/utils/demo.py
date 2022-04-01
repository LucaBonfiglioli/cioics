from pathlib import Path

from choixe import XConfig

this_folder = Path(__file__).parent
cfg = XConfig.from_file(this_folder / "utils.yml")
cfg.process().save_to(this_folder / "out.yml")
