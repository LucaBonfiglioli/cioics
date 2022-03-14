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
    """A configuration with superpowers!"""

    PRIVATE_KEYS = ["_filename", "_schema"]
    """Keys to exclude in visiting operations"""

    def __init__(
        self,
        filename: Optional[Union[str, Path]] = None,
        plain_dict: Optional[Dict] = None,
        schema: Optional[Schema] = None,
    ):
        """Constructor for `XConfig`

        Args:
            filename (Optional[Union[str, Path]], optional): An optional path to load
            the configuration from a file. Supported formats include yaml and json.
            Defaults to None.
            plain_dict (Optional[Dict], optional): An optional dict, in case the data
            is already loaded. Defaults to None.
            schema (Optional[Schema], optional): Python schema object used for
            validation. Defaults to None.
        """

        # options
        self._filename = Path(filename) if filename is not None else None
        self._schema = None

        if plain_dict is not None:
            data = plain_dict
        elif self._filename is not None:
            data = load(self._filename)
        else:
            data = {}

        self.update(data)
        self.set_schema(schema)

    def get_schema(self) -> Optional[Schema]:
        """Getter for the configuration schema"""
        return self._schema

    def set_schema(self, s: Schema) -> None:
        """Setter for the configuration schema"""
        if s is not None:
            assert isinstance(s, Schema), "schema is not a valid Schema object!"
        self._schema = s

    def get_filename(self) -> Optional[Path]:
        """Getter for the configuration filename"""
        return self._filename

    def copy(self) -> XConfig:
        """Prototype method to copy this `XConfig` object.

        Returns:
            XConfig: A deepcopy of this `XConfig`.
        """
        return XConfig(
            filename=self.get_filename(),
            plain_dict=self.to_dict(),
            schema=self.get_schema(),
        )

    def validate(self, replace: bool = True):
        """Validate internal schema if any

        Args:
            replace (bool, optional): True to replace internal dictionary with
            force-validated fields (e.g. Schema.Use). Defaults to True.
        """

        if self.get_schema() is not None:
            new_dict = self.get_schema().validate(self.to_dict())
            if replace:
                self.update(new_dict)

    def is_valid(self) -> bool:
        """Check for schema validity

        Returns:
            bool: True for valid or no schema inside
        """
        if self.get_schema() is not None:
            return self.get_schema().is_valid(self.to_dict())
        return True

    def save_to(self, filename: str) -> None:
        """Save configuration to output file

        Args:
            filename (str): output filename
        """
        filename = Path(filename)
        data = decode(self.parse())
        dump(data, filename)

    def deep_get(
        self, full_key: Union[str, list], default: Optional[Any] = None
    ) -> Any:
        """Gets value based on full path key (dot notation like 'a.b.0.d' or list ['a','b','0','d'])

        Args:
            full_key (Union[str, list]): full path key in pydash notation.
            default (Optional[Any], optional): result in case the path is not present.
            Defaults to None.

        Returns:
            Any: The value at the specified path.
        """
        return py_.get(self, full_key, default=default)

    def deep_set(
        self, full_key: Union[str, list], value: Any, only_valid_keys: bool = True
    ) -> None:
        """Sets value based on full path key (dot notation like 'a.b.0.d' or list
        ['a','b','0','d'])

        Args:
            full_key (Union[str, list]): Full path key in pydash notation.
            value (Any): The value to set.
            only_valid_keys (bool, optional): True to avoid set on not present keys.
            Defaults to True.
        """

        if only_valid_keys:
            if py_.has(self, full_key):
                py_.set_(self, full_key, value)
        else:
            py_.set_(self, full_key, value)

    def deep_update(self, data: Dict, full_merge: bool = False):
        """Updates current confing in depth, based on keys of other input dictionary.
        It is used to replace nested keys with new ones, but can also be used as a merge
        of two completely different XConfig if `full_merge`=True.

        Args:
            data (Dict): An other dictionary to use as data source.
            full_merge (bool, optional): False to replace only the keys that are
            actually present. Defaults to False.
        """

        other_chunks = walk(parse(data))
        for key, new_value in other_chunks:
            self.deep_set(key, new_value, only_valid_keys=not full_merge)

    def parse(self) -> Node:
        """Parse this object into a Choixe AST Node.

        Returns:
            Node: The parsed node.
        """
        sanitized = dict(self)
        [sanitized.pop(x) for x in self.PRIVATE_KEYS]
        return parse(sanitized)

    def to_dict(self) -> Dict:
        """Convert this XConfig to a plain python dictionary. Also converts some nodes
        like numpy arrays into plain lists.

        Returns:
            Dict: The decoded dictionary.
        """
        return decode(self.parse())

    def walk(self) -> List[Tuple[List[Union[str, int]], Any]]:
        """Perform the walk operation on this XConfig.

        Returns:
            List[Tuple[List[Union[str, int]], Any]]: The walk output.
        """
        return walk(self.parse())

    def _process(
        self, context: Optional[Dict[str, Any]] = None, allow_branching: bool = True
    ) -> List[XConfig]:
        cwd = self._filename.parent if self._filename is not None else None
        data = process(
            self.parse(), context=context, cwd=cwd, allow_branching=allow_branching
        )
        return [XConfig(filename=self._filename, plain_dict=x) for x in data]

    def process(self, context: Optional[Dict[str, Any]] = None) -> XConfig:
        """Process this XConfig without branching.

        Args:
            context (Optional[Dict[str, Any]], optional): Optional data structure
            containing all variables values. Defaults to None.

        Returns:
            XConfig: The processed XConfig.
        """
        return self._process(context=context, allow_branching=False)[0]

    def process_all(self, context: Optional[Dict[str, Any]] = None) -> List[XConfig]:
        """Process this XConfig with branching.

        Args:
            context (Optional[Dict[str, Any]], optional): Optional data structure
            containing all variables values. Defaults to None.

        Returns:
            List[XConfig]: A list of all processing outcomes.
        """
        return self._process(context=context, allow_branching=True)
