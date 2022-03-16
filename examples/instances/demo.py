from pathlib import Path

import rich
from cioics import XConfig

# Path to the folder containing this file
this_folder = Path(__file__).parent


# Load an XConfig
cfg = XConfig(this_folder / "config.yml")

rich.print("Loaded XConfig: ")
rich.print(cfg.to_dict())

rich.print("Parsed XConfig: ")
rich.print(cfg.parse())

rich.print("Processed XConfig: ")
rich.print(cfg.process())
