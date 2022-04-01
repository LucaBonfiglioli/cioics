from pathlib import Path
from traceback import print_exc

import rich
from choixe import XConfig

this_folder = Path(__file__).parent
files = [
    "wrong_directive.yml",
    "not_yaml.yml",
    "not_dict.yml",
    "wrong_syntax_inline.yml",
]
for file in files:
    try:
        path = this_folder / file
        cfg = XConfig.from_file(path)
        cfg.process_all()
    except Exception as e:
        rich.print(f"File:", path)
        print_exc()
