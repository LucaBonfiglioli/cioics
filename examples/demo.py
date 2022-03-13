from cioics import XConfig
from pathlib import Path

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

# Process the configuration, replacing variables, importing files, performing sweeps, etc...
all_cfgs = cfg.process_all(context=context)

# Save the output configurations to a folder named "outputs"
for i, x in enumerate(all_cfgs):
    x.save_to(this_folder / "outputs" / f"output_{str(i).zfill(4)}.yml")
