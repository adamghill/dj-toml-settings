import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import toml
from dateutil import parser as dateparser
from typeguard import typechecked

from dj_toml_settings.value_parsers.dict_parsers import (
    EnvParser,
    InsertParser,
    NoneParser,
    PathParser,
    TypeParser,
    ValueParser,
)
from dj_toml_settings.value_parsers.str_parsers import VariableParser

logger = logging.getLogger(__name__)


class Parser:
    path: Path
    data: dict

    def __init__(self, path: Path, data: dict | None = None):
        self.path = path
        self.data = data or {}

    @typechecked
    def parse_file(self):
        """Parse data from the specified TOML file to use for Django settings.

        The sections get parsed in the following order with the later sections overriding the earlier:
        1. `[tool.django]`
        2. `[tool.django.apps.*]`
        3. `[tool.django.envs.{ENVIRONMENT}]` where {ENVIRONMENT} is defined in the `ENVIRONMENT` env variable
        """

        toml_data = self.get_data()

        # Get potential settings from `tool.django.apps` and `tool.django.envs`
        apps_data = toml_data.pop("apps", {})
        envs_data = toml_data.pop("envs", {})

        # Add default settings from `tool.django`
        for key, value in toml_data.items():
            logger.debug(f"tool.django: Update '{key}' with '{value}'")

            self.data.update({key: self.parse_value(key, value)})

        # Add settings from `tool.django.apps.*`
        for apps_name, apps_value in apps_data.items():
            for app_key, app_value in apps_value.items():
                logger.debug(f"tool.django.apps.{apps_name}: Update '{app_key}' with '{app_value}'")

                self.data.update({app_key: self.parse_value(app_key, app_value)})

        # Add settings from `tool.django.envs.*` if it matches the `ENVIRONMENT` env variable
        if environment_env_variable := os.getenv("ENVIRONMENT"):
            for envs_name, envs_value in envs_data.items():
                if environment_env_variable == envs_name:
                    for env_key, env_value in envs_value.items():
                        logger.debug(f"tool.django.envs.{envs_name}: Update '{env_key}' with '{env_value}'")

                        self.data.update({env_key: self.parse_value(env_key, env_value)})

        return self.data

    @typechecked
    def get_data(self) -> dict:
        """Gets the data from the passed-in TOML file."""

        data = {}

        try:
            data = toml.load(self.path)
        except FileNotFoundError:
            logger.warning(f"Cannot find file at: {self.path}")
        except toml.TomlDecodeError:
            logger.error(f"Cannot parse TOML at: {self.path}")

        return data.get("tool", {}).get("django", {}) or {}

    @typechecked
    def parse_value(self, key: Any, value: Any) -> Any:
        """Handle special cases for `value`.

        Special cases:
        - `dict` keys
            - `$env`: retrieves an environment variable; optional `default` argument
            - `$path`: converts string to a `Path`; handles relative path
            - `$insert`: inserts the value to an array; optional `index` argument
            - `$none`: inserts the `None` value
            - `$value`: literal value
            - `$type`: casts the value to a particular type
        - variables in `str`
        - `datetime`
        """

        if isinstance(value, list):
            # Process each item in the list
            processed_list = []

            for item in value:
                processed_item = self.parse_value(key, item)
                processed_list.append(processed_item)

            value = processed_list
        elif isinstance(value, dict):
            # Process nested dictionaries
            processed_dict = {}

            for k, v in value.items():
                if isinstance(v, dict):
                    processed_dict.update({k: self.parse_value(key, v)})
                else:
                    processed_dict[k] = v

            value = processed_dict

            type_parser = TypeParser(data=self.data, value=value)
            env_parser = EnvParser(data=self.data, value=value)
            path_parser = PathParser(data=self.data, value=value, path=self.path)
            value_parser = ValueParser(data=self.data, value=value)
            none_parser = NoneParser(data=self.data, value=value)
            insert_parser = InsertParser(data=self.data, value=value, data_key=key)

            # Check for a match for all operators (except $type)
            for parser in [env_parser, path_parser, value_parser, insert_parser, none_parser]:
                if parser.match():
                    value = parser.parse()
                    break

            # Parse $type last because it can operate on the resolved value from the other parsers
            if type_parser.match():
                value = type_parser.parse(value)
        elif isinstance(value, str):
            value = VariableParser(data=self.data, value=value).parse()
        elif isinstance(value, datetime):
            value = dateparser.isoparse(str(value))

        return value
