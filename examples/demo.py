from pathlib import Path

import rich
from cioics import XConfig

# Path to the folder containing this file
this_folder = Path(__file__).parent

# The values to be replaced when using $var(...)
# Can be a nested structure
context = {
    "hparams": {
        "lr": 0.001,
        "num_epochs": 600,
        "normalize": True,
    },
    "data": {
        "num_classes1": 8,
        "num_classes2": 4,
    },
}

# Load an XConfig
cfg = XConfig(this_folder / "neural_network.yml")

rich.print("Loaded XConfig: ")
rich.print(cfg.to_dict())

rich.print("Parsed XConfig: ")
rich.print(cfg.parse())

# Process the configuration, replacing variables, importing files, performing sweeps, etc...
all_cfgs = cfg.process_all(context=context)

# Save the output configurations to a folder named "outputs"
for i, x in enumerate(all_cfgs):
    path = this_folder / "outputs" / f"output_{str(i).zfill(4)}.yml"
    rich.print(f"Saving a configuration to {path}")
    x.save_to(path)
