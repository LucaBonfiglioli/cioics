from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pydash as py_
from box import Box
from schema import Schema

from cioics.ast.nodes import Node
from cioics.ast.parser import parse
from cioics.utils.io import dump, load
from cioics.visitors import decode, process, walk


class XConfig(Box):
    PRIVATE_KEYS = ["_filename", "_schema"]

    def __init__(
        self,
        filename: Optional[Union[str, Path]] = None,
        plain_dict: Optional[Dict] = None,
    ):
        """Creates a XConfig object from configuration file
        :param filename: configuration file [yaml, json, toml], defaults to None
        :type filename: str, optional
        :param plain_dict: if not None will be used as data source instead of filename, defaults to None
        :type plain_dict: dict, optional
        """

        # options
        self._filename = None

        if plain_dict is None:
            if filename is not None:
                self._filename = Path(filename)
                self.update(load(self._filename))
        else:
            self.update(plain_dict)

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

    def save_to(self, filename: str) -> None:
        """Save configuration to output file
        :param filename: output filename
        :type filename: str
        :raises NotImplementedError: Raise error for unrecognized extension
        """
        filename = Path(filename)
        data = decode(self.parse())
        dump(data, filename)

    def deep_get(self, full_key: Union[str, list], default: Optional[Any] = None):
        """Gets value based on full path key (dot notation like 'a.b.0.d' or list ['a','b','0','d'])

        :param full_key: full path key as dotted string or list of chunks
        :type full_key: str | list
        """
        return py_.get(self, full_key, default=default)

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
            if py_.has(self, full_key):
                py_.set_(self, full_key, value)
        else:
            py_.set_(self, full_key, value)

    def deep_update(self, data: Dict, full_merge: bool = False):
        """Updates current confing in depth, based on keys of other input dictionary.
        It is used to replace nested keys with new ones, but can also be used as a merge
        of two completely different XConfig if `full_merge`=True


        :param other: other dictionary to use as data source
        :type other: dict
        :param full_merge: FALSE to replace only the keys that are actually present
        :type full_merge: bool
        """

        other_chunks = walk(parse(data))
        for key, new_value in other_chunks:
            self.deep_set(key, new_value, only_valid_keys=not full_merge)

    def parse(self) -> Node:
        sanitized = dict(self)
        [sanitized.pop(x) for x in self.PRIVATE_KEYS]
        return parse(sanitized)

    def to_dict(self) -> Dict:
        return decode(self.parse())

    def walk(self) -> List[Tuple[List[Union[str, int]], Any]]:
        return walk(self.parse())

    def process(self) -> List[XConfig]:
        return [XConfig(plain_dict=x) for x in process(self.parse())]
