import logging
import os
import re
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dateutil import parser as dateparser
from typeguard import typechecked

from dj_toml_settings.exceptions import InvalidActionError

logger = logging.getLogger(__name__)


class DictParser:
    data: dict
    value: dict
    key: str

    def __init__(self, data: dict, value: dict):
        self.data = data
        self.value = value

        if not hasattr(self, "key"):
            raise NotImplementedError("Missing key attribute")

        self.key = self.add_prefix_to_key(self.key)

    def match(self) -> bool:
        return self.key in self.value

    @typechecked
    def add_prefix_to_key(self, key: str) -> str:
        """Gets the key for the special operator."""

        return f"${key}"

    def parse(self, *args, **kwargs):
        raise NotImplementedError("parse() not implemented")


class EnvParser(DictParser):
    key: str = "env"

    def parse(self) -> Any:
        default_special_key = self.add_prefix_to_key("default")
        default_value = self.value.get(default_special_key)

        env_value = self.value[self.key]
        value = os.getenv(env_value, default_value)

        return value


class PathParser(DictParser):
    key: str = "path"

    def __init__(self, data: dict, value: dict, path: Path):
        super().__init__(data, value)
        self.path = path

    def parse(self) -> Any:
        self.file_name = self.value[self.key]
        value = self.resolve_file_name()

        return value

    @typechecked
    def resolve_file_name(self) -> Path:
        """Parse a path string relative to a base path.

        Args:
            file_name: Relative or absolute file name.
            path: Base path to resolve file_name against.
        """

        current_path = Path(self.path).parent if self.path.is_file() else self.path

        return Path((current_path / self.file_name).resolve())


class ValueParser(DictParser):
    key = "value"

    def parse(self) -> Any:
        return self.value[self.key]


class InsertParser(DictParser):
    key = "insert"

    def __init__(self, data: dict, value: dict, data_key: str):
        super().__init__(data, value)
        self.data_key = data_key

    def parse(self) -> Any:
        insert_data = self.data.get(self.data_key, [])

        # Check the existing value is an array
        if not isinstance(insert_data, list):
            raise InvalidActionError(f"`insert` cannot be used for value of type: {type(self.data[self.data_key])}")

        # Insert the data
        index_key = self.add_prefix_to_key("index")
        index = self.value.get(index_key, len(insert_data))

        insert_data.insert(index, self.value[self.key])

        return insert_data


class NoneParser(DictParser):
    key = "none"

    def match(self) -> bool:
        return super().match() and self.value.get(self.key) is not None

    def parse(self) -> Any:
        return None


class TypeParser(DictParser):
    key = "type"

    def parse(self, resolved_value: Any) -> Any:
        value_type = self.value[self.key]

        if not isinstance(value_type, str):
            raise ValueError(f"Type must be a string, got {type(value_type).__name__}")

        try:
            if value_type == "bool":
                if isinstance(resolved_value, str):
                    resolved_value = resolved_value.lower() == "true"
                elif isinstance(resolved_value, int):
                    resolved_value = bool(resolved_value)
                else:
                    raise ValueError(f"Type must be a string or int, got {type(resolved_value).__name__}")

                return bool(resolved_value)
            elif value_type == "int":
                return int(resolved_value)
            elif value_type == "str":
                return str(resolved_value)
            elif value_type == "float":
                return float(resolved_value)
            elif value_type == "decimal":
                return Decimal(str(resolved_value))
            elif value_type == "datetime":
                return dateparser.parse(resolved_value)
            elif value_type == "date":
                result = dateparser.parse(resolved_value)

                return result.date()
            elif value_type == "time":
                result = dateparser.parse(resolved_value)

                return result.time()
            elif value_type == "timedelta":
                return parse_timedelta(resolved_value)
            elif value_type == "url":
                return urlparse(str(resolved_value))
            else:
                raise ValueError(f"Unsupported type: {value_type}")
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Failed to convert {resolved_value!r} to {value_type}: {e}")

            raise ValueError(f"Failed to convert {resolved_value!r} to {value_type}: {e}") from e


def parse_timedelta(value):
    if isinstance(value, int | float):
        return timedelta(seconds=value)
    elif not isinstance(value, str):
        raise ValueError(f"Unsupported type for timedelta: {type(value).__name__}")

    # Pattern to match both space-separated and combined formats like '7w2d'
    pattern = r"(?:\s*(\d+\.?\d*)([u|ms|s|m|h|d|w]+))"
    matches = re.findall(pattern, value, re.IGNORECASE)

    if not matches and value.strip():
        raise ValueError(f"Invalid timedelta format: {value}")

    unit_map = {
        "u": "microseconds",
        "ms": "milliseconds",
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
        "w": "weeks",
    }
    kwargs = {}

    for num_str, unit in matches:
        try:
            num = float(num_str)
        except ValueError as e:
            raise ValueError(f"Invalid number in timedelta: {num_str}") from e

        if unit not in unit_map:
            raise ValueError(f"Invalid time unit: {unit}")

        key = unit_map[unit]
        kwargs[key] = kwargs.get(key, 0) + num

    return timedelta(**kwargs)
