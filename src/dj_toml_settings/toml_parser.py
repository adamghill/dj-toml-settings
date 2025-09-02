import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import toml
from dateutil import parser as dateparser
from typeguard import typechecked

from dj_toml_settings.value_parsers.dict_value_parsers import (
    EnvValueParser,
    InsertValueParser,
    NoneValueParser,
    PathValueParser,
    TypeValueParser,
    ValueValueParser,
)

logger = logging.getLogger(__name__)


@typechecked
def combine_bookends(original: str, match: re.Match, middle: Any) -> str:
    """Get the beginning of the original string before the match, and the
    end of the string after the match and smush the replaced value in between
    them to generate a new string.
    """

    start_idx = match.start()
    start = original[:start_idx]

    end_idx = match.end()
    ending = original[end_idx:]

    return start + str(middle) + ending


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

            self.data.update(self.parse_key_value(key, value))

        # Add settings from `tool.django.apps.*`
        for apps_name, apps_value in apps_data.items():
            for app_key, app_value in apps_value.items():
                logger.debug(f"tool.django.apps.{apps_name}: Update '{app_key}' with '{app_value}'")

                self.data.update(self.parse_key_value(app_key, app_value))

        # Add settings from `tool.django.envs.*` if it matches the `ENVIRONMENT` env variable
        if environment_env_variable := os.getenv("ENVIRONMENT"):
            for envs_name, envs_value in envs_data.items():
                if environment_env_variable == envs_name:
                    for env_key, env_value in envs_value.items():
                        logger.debug(f"tool.django.envs.{envs_name}: Update '{env_key}' with '{env_value}'")

                        self.data.update(self.parse_key_value(env_key, env_value))

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
    def parse_key_value(self, key: str, value: Any) -> dict:
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

        if isinstance(value, dict):
            type_parser = TypeValueParser(data=self.data, value=value)
            env_parser = EnvValueParser(data=self.data, value=value)
            path_parser = PathValueParser(data=self.data, value=value, path=self.path)
            value_parser = ValueValueParser(data=self.data, value=value)
            none_parser = NoneValueParser(data=self.data, value=value)
            insert_parser = InsertValueParser(data=self.data, value=value, data_key=key)

            # Check for a match for all specials (except $type)
            for parser in [env_parser, path_parser, value_parser, insert_parser, none_parser]:
                if parser.match():
                    value = parser.parse()
                    break

            # Parse $type last because it can operate on the resolved value from the other parsers
            if type_parser.match():
                value = type_parser.parse(value)
        elif isinstance(value, str):
            # Handle variable substitution
            for match in re.finditer(r"\$\{\w+\}", value):
                data_key = value[match.start() : match.end()][2:-1]

                if variable := self.data.get(data_key):
                    if isinstance(variable, Path):
                        path_str = combine_bookends(value, match, variable)

                        value = Path(path_str)
                    elif callable(variable):
                        value = variable
                    elif isinstance(variable, int):
                        value = combine_bookends(value, match, variable)

                        try:
                            value = int(value)
                        except Exception:  # noqa: S110
                            pass
                    elif isinstance(variable, float):
                        value = combine_bookends(value, match, variable)

                        try:
                            value = float(value)
                        except Exception:  # noqa: S110
                            pass
                    elif isinstance(variable, list):
                        value = variable
                    elif isinstance(variable, dict):
                        value = variable
                    elif isinstance(variable, datetime):
                        value = dateparser.isoparse(str(variable))
                    else:
                        value = value.replace(match.string, str(variable))
                else:
                    logger.warning(f"Missing variable substitution {value}")
        elif isinstance(value, datetime):
            value = dateparser.isoparse(str(value))

        return {key: value}
