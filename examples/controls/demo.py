from pathlib import Path

import rich
from choixe import XConfig

# Path to the folder containing this file
this_folder = Path(__file__).parent

# Load an XConfig
context = {
    "params": {
        "cats": [
            {"name": "Luna", "age": 5},
            {"name": "Milo", "age": 6},
            {"name": "Oliver", "age": 14},
        ]
    }
}
cfg = XConfig.from_file(this_folder / "loops.yml")

# Process
result = cfg.process(context=context)

rich.print("Processed XConfig: ")
rich.print(result)

result.save_to(this_folder / "output.yml")
