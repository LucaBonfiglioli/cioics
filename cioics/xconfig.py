from __future__ import annotations

import os
from box.from_file import converters
from box import box_from_file, Box, BoxList
import numpy as np
import pydash
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from schema import Schema
from pathlib import Path
import copy

from choixe.sweepers import Sweeper


class XConfig(Box):
    KNOWN_EXTENSIONS = converters.keys()
    PRIVATE_KEYS = ["_filename", "_schema"]

    def __init__(self, filename: str = None, **kwargs):
        """Creates a XConfig object from configuration file
        :param filename: configuration file [yaml, json, toml], defaults to None
        :type filename: str, optional
        :param plain_dict: if not None will be used as data source instead of filename, defaults to None
        :type plain_dict: dict, optional
        """

        # options
        _dict = kwargs.get("plain_dict", None)
        self._filename = None

        if _dict is None:
            if filename is not None:
                self._filename = Path(filename)
                self.update(box_from_file(file=Path(filename)))
        else:
            self.update(_dict)

        self._schema: Optional[Schema] = None

    def copy(self) -> "XConfig":
        """Prototype copy

        :return: deep copy of source XConfig
        :rtype: XConfig
        """

        new_xconfig = XConfig(filename=None)
        new_xconfig.update(self.to_dict())
        new_xconfig._filename = self._filename
        new_xconfig._schema = self._schema
        return new_xconfig

    @property
    def schema(self) -> Optional[Schema]:
        return self._schema

    @schema.setter
    def schema(self, s: Schema) -> None:
        """Push validation schema
        :param schema: validation schema
        :type schema: Schema
        """
        if s is not None:
            assert isinstance(s, Schema), "schema is not a valid Schema object!"
        self._schema = s

    def validate(self, replace: bool = True):
        """Validate internal schema if any

        :param replace: TRUE to replace internal dictionary with force-validated fields (e.g. Schema.Use)
        :type replace: bool
        """

        if self.schema is not None:
            new_dict = self.schema.validate(self.to_dict())
            if replace:
                self.update(new_dict)

    def is_valid(self) -> bool:
        """Check for schema validity
        :return: TRUE for valid or no schema inside
        :rtype: bool
        """
        if self.schema is not None:
            return self.schema.is_valid(self.to_dict())
        return True

    def save_to(self, filename: str):
        """Save configuration to output file
        :param filename: output filename
        :type filename: str
        :raises NotImplementedError: Raise error for unrecognized extension
        """
        filename = Path(filename)
        data = self.to_dict()
        if "yml" in filename.suffix.lower() or "yaml" in filename.suffix.lower():
            Box(self.decode(data)).to_yaml(filename=filename)
        elif "json" in filename.suffix.lower():
            Box(self.decode(data)).to_json(filename=filename)
        elif "toml" in filename.suffix.lower():
            Box(self.decode(data)).to_toml(filename=filename)
        else:
            raise NotImplementedError(
                f"Extension {filename.suffix.lower()} not supported yet!"
            )

    @classmethod
    def decode(cls, data: any) -> any:
        """Decode decodable data

        :param data: [description]
        :type data: any
        :return: [description]
        :rtype: any
        """
        if isinstance(data, np.ndarray):
            return cls.decode(data.tolist())
        elif "numpy" in str(type(data)):
            return cls.decode(data.item())
        elif isinstance(data, list) or isinstance(data, BoxList):
            return [cls.decode(x) for x in data]
        elif isinstance(data, tuple):
            return [cls.decode(x) for x in data]
        elif isinstance(data, dict) or isinstance(data, Box):
            return {k: cls.decode(x) for k, x in data.items()}
        else:
            return data

    def deep_set(
        self, full_key: Union[str, list], value: any, only_valid_keys: bool = True
    ):
        """Sets value based on full path key (dot notation like 'a.b.0.d' or list ['a','b','0','d'])

        :param full_key: full path key as dotted string or list of chunks
        :type full_key: str | list
        :param value: value to set
        :type value: any
        :param only_valid_keys: TRUE to avoid set on not present keys
        :type only_valid_keys: bool
        """

        if only_valid_keys:
            if pydash.has(self, full_key):
                pydash.set_(self, full_key, value)
        else:
            pydash.set_(self, full_key, value)

    def deep_update(self, other: "XConfig", full_merge: bool = False):
        """Updates current confing in depth, based on keys of other input XConfig.
        It is used to replace nested keys with new ones, but can also be used as a merge
        of two completely different XConfig if `full_merge`=True


        :param other: other XConfig to use as data source
        :type other: XConfig
        :param full_merge: FALSE to replace only the keys that are actually present
        :type full_merge: bool
        """

        other_chunks = other.chunks_as_lists(discard_private_qualifiers=True)
        for key, new_value in other_chunks:
            self.deep_set(key, new_value, only_valid_keys=not full_merge)

    def to_dict(self, discard_private_qualifiers: bool = True) -> Dict:
        """
        Turn the Box and sub Boxes back into a native python dictionary.
        :return: python dictionary of this Box
        """
        out_dict = copy.deepcopy(dict(self))
        for k, v in out_dict.items():
            if isinstance(v, Box):
                out_dict[k] = self.decode(v.to_dict())
            elif isinstance(v, BoxList):
                out_dict[k] = self.decode(v.to_list())

        if discard_private_qualifiers:
            chunks = self.chunks_as_lists(discard_private_qualifiers=False)
            for key, value in chunks:
                if any([x for x in self.PRIVATE_KEYS if x in key]):
                    pydash.unset(out_dict, key)

        return out_dict

    def available_placeholders(
        self,
        ignore_defaults: bool = False,
    ) -> Dict[str, Placeholder]:
        """Retrieves the available placeholders list

        :param ignore_defaults: TRUE to ignore placeholders with default
        :type: ignore_defaults: bool

        :return: list of found (str,str) pairs
        :rtype: Tuple[str,str]
        """

        chunks = self.chunks_as_tuples(discard_private_qualifiers=True)
        placeholders = {}
        for k, v in chunks:
            if self.is_a_placeholder(v):
                key = ".".join(k)
                placelholder = Placeholder.from_string(v)
                if ignore_defaults and placelholder.default_value is not None:
                    continue
                placeholders[key] = placelholder
        return placeholders

    def check_available_placeholders(
        self,
        close_app: bool = False,
        ignore_defaults: bool = False,
    ) -> bool:
        """Check for available placeholder and close app if necessary
        :param close_app: TRUE to close app if at least one placeholder found, defaults to False
        :type close_app: bool, optional
        :param ignore_defaults: TRUE to ignore placeholders with default
        :type: ignore_defaults: bool

        :return: TRUE if no placeholders found
        :rtype: bool
        """
        placeholders = self.available_placeholders(ignore_defaults=ignore_defaults)
        if len(placeholders) > 0:
            import rich
            from rich.table import Table
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Placeholder", style="dim")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Options")
            table.add_column("Default")

            header = "*** Incomplete Configuration, Placeholders found! ***"
            rich.print(Markdown(f"# {header}"))

            for k, p in placeholders.items():
                if p.is_valid():
                    table.add_row(
                        k, p.name, p.plain_type, "|".join(p.options), p.default_value
                    )

            console.print(table)

            if close_app:
                import sys

                sys.exit(1)
            return False
        return True

    @classmethod
    def from_dict(cls, d: dict, **kwargs) -> "XConfig":
        """Creates XConfig from a plain dictionary
        : param d: input dictionary
        : type d: dict
        : return: built XConfig
        : rtype: XConfig
        """
        cfg = XConfig(filename=None, plain_dict=d, **kwargs)
        return cfg

    @classmethod
    def _add_key_to_path(cls, key_to_add: any, path: Sequence[any]):
        path.append(str(key_to_add))

    @classmethod
    def _walk(
        cls,
        d: Dict,
        path: Sequence = None,
        chunks: Sequence = None,
        discard_private_qualifiers: bool = True,
    ) -> Sequence[Tuple[str, Any]]:
        """Deep visit of dictionary building a plain sequence of pairs(key, value) where key has a pydash notation
        : param d: input dictionary
        : type d: Dict
        : param path: private output value for path(not use), defaults to None
        : type path: Sequence, optional
        : param chunks: private output to be fileld with retrieved pairs(not use), defaults to None
        : type chunks: Sequence, optional
        : param discard_private_qualifiers: TRUE to discard keys starting with private qualifier, defaults to True
        : type discard_private_qualifiers: bool, optional
        : return: sequence of retrieved pairs
        : rtype: Sequence[Tuple[str, Any]]
        """
        root = False
        if path is None:
            path, chunks, root = [], [], True
        if isinstance(d, dict):
            for k, v in d.items():
                cls._add_key_to_path(k, path)
                if isinstance(v, dict) or isinstance(v, list):
                    cls._walk(
                        v,
                        path=path,
                        chunks=chunks,
                        discard_private_qualifiers=discard_private_qualifiers,
                    )
                else:
                    keys = list(map(str, path))
                    if not (
                        discard_private_qualifiers
                        and any([x for x in cls.PRIVATE_KEYS if x in keys])
                    ):
                        chunks.append((keys, v))
                path.pop()
        elif isinstance(d, list):
            for idx, v in enumerate(d):
                cls._add_key_to_path(idx, path)
                cls._walk(
                    v,
                    path=path,
                    chunks=chunks,
                    discard_private_qualifiers=discard_private_qualifiers,
                )
                path.pop()
        else:
            keys = list(map(str, path))
            chunks.append((keys, d))
        if root:
            return chunks
