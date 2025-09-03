import os
from pathlib import Path
from typing import Any

from typeguard import typechecked

from dj_toml_settings.exceptions import InvalidActionError


class DictParser:
    data: dict
    value: str

    def __init__(self, data: dict, value: str):
        self.data = data
        self.value = value

        if not self.key:
            raise NotImplementedError("Missing key")

        self.key = self.add_prefix_and_suffix_to_key(self.key)

    def match(self) -> bool:
        return self.key in self.value

    @typechecked
    def add_prefix_and_suffix_to_key(self, key: str) -> str:
        """Gets the key for the special operator. Defaults to "$" as the prefix, and "" as the suffix.

        To change in the included TOML settings, set:
        ```
        TOML_SETTINGS_SPECIAL_PREFIX = ""
        TOML_SETTINGS_SPECIAL_SUFFIX = ""
        ```
        """

        prefix = self.data.get("TOML_SETTINGS_SPECIAL_PREFIX", "$")
        suffix = self.data.get("TOML_SETTINGS_SPECIAL_SUFFIX", "")

        return f"{prefix}{key}{suffix}"

    def parse(self):
        raise NotImplementedError("parse() not implemented")


class EnvParser(DictParser):
    key: str = "env"

    def parse(self) -> Any:
        default_special_key = self.add_prefix_and_suffix_to_key("default")
        default_value = self.value.get(default_special_key)

        env_value = self.value[self.key]
        value = os.getenv(env_value, default_value)

        return value


class PathParser(DictParser):
    key: str = "path"

    def __init__(self, data: dict, value: str, path: Path):
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

        return (current_path / self.file_name).resolve()


class ValueParser(DictParser):
    key = "value"

    def parse(self) -> Any:
        return self.value[self.key]


class InsertParser(DictParser):
    key = "insert"

    def __init__(self, data: dict, value: str, data_key: str):
        super().__init__(data, value)
        self.data_key = data_key

    def parse(self) -> Any:
        insert_data = self.data.get(self.data_key, [])

        # Check the existing value is an array
        if not isinstance(insert_data, list):
            raise InvalidActionError(f"`insert` cannot be used for value of type: {type(self.data[self.data_key])}")

        # Insert the data
        index_key = self.add_prefix_and_suffix_to_key("index")
        index = self.value.get(index_key, len(insert_data))

        insert_data.insert(index, self.value[self.key])

        return insert_data


class NoneParser(DictParser):
    key = "none"

    def match(self) -> bool:
        return super().match() and self.value.get(self.key)

    def parse(self) -> Any:
        return None


class TypeParser(DictParser):
    key = "type"

    def parse(self, resolved_value: Any) -> Any:
        value_type = self.value[self.key]

        if value_type == "bool":
            if isinstance(resolved_value, str):
                if resolved_value == "False":
                    resolved_value = False
                elif resolved_value == "True":
                    resolved_value = True
            elif isinstance(resolved_value, int):
                if resolved_value == 0:
                    resolved_value = False
                elif resolved_value == 1:
                    resolved_value = True
        # TODO: add other types similar to environs

        return resolved_value
