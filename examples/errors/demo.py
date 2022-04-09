from pathlib import Path

import rich
from choixe import XConfig

this_folder = Path(__file__).parent
files = [
    # "wrong_directive.yml",
    # "not_dict.yml",
    # "wrong_syntax_inline.yml",
    # "missing_arguments.yml",
    # "excessive_arguments.yml",
    # "invalid_arguments.yml",
]
context = XConfig.from_file(this_folder / "context.yml")

for file in files:
    try:
        path = this_folder / file
        cfg = XConfig.from_file(path)
        result = cfg.process_all(context=context)
        rich.print(result)
    except Exception as e:
        rich.print(f'ERROR in file: "{path}"')
        rich.print(e)
        rich.print()
