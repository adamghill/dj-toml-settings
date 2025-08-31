import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import toml
from dateutil import parser as dateparser
from typeguard import typechecked

from dj_toml_settings.exceptions import InvalidActionError

logger = logging.getLogger(__name__)


@typechecked
def parse_file(path: Path, data: dict | None = None):
    """Parse data from the specified TOML file to use for Django settings.

    The sections get parsed in the following order with the later sections overriding the earlier:
    1. `[tool.django]`
    2. `[tool.django.apps.*]`
    3. `[tool.django.envs.{ENVIRONMENT}]` where {ENVIRONMENT} is defined in the `ENVIRONMENT` env variable
    """

    toml_data = get_data(path)
    data = data or {}

    # Get potential settings from `tool.django.apps` and `tool.django.envs`
    apps_data = toml_data.pop("apps", {})
    envs_data = toml_data.pop("envs", {})

    # Add default settings from `tool.django`
    for key, value in toml_data.items():
        logger.debug(f"tool.django: Update '{key}' with '{value}'")

        data.update(parse_key_value(data, key, value, path))

    # Add settings from `tool.django.apps.*`
    for apps_name, apps_value in apps_data.items():
        for app_key, app_value in apps_value.items():
            logger.debug(f"tool.django.apps.{apps_name}: Update '{app_key}' with '{app_value}'")

            data.update(parse_key_value(data, app_key, app_value, path))

    # Add settings from `tool.django.envs.*` if it matches the `ENVIRONMENT` env variable
    if environment_env_variable := os.getenv("ENVIRONMENT"):
        for envs_name, envs_value in envs_data.items():
            if environment_env_variable == envs_name:
                for env_key, env_value in envs_value.items():
                    logger.debug(f"tool.django.envs.{envs_name}: Update '{env_key}' with '{env_value}'")

                    data.update(parse_key_value(data, env_key, env_value, path))

    return data


@typechecked
def get_data(path: Path) -> dict:
    """Gets the data from the passed-in TOML file."""

    data = {}

    try:
        data = toml.load(path)
    except FileNotFoundError:
        logger.warning(f"Cannot find file at: {path}")
    except toml.TomlDecodeError:
        logger.error(f"Cannot parse TOML at: {path}")

    return data.get("tool", {}).get("django", {}) or {}


@typechecked
def parse_key_value(data: dict, key: str, value: Any, path: Path) -> dict:
    """Handle special cases for `value`.

    Special cases:
    - `dict` keys
        - `$env`: retrieves an environment variable; optional `default` argument
        - `$path`: converts string to a `Path`; handles relative path
        - `$insert`: inserts the value to an array; optional `index` argument
        - `$none`: inserts the `None` value
    - variables in `str`
    - `datetime`
    """

    if isinstance(value, dict):
        # Defaults to "$env" and "$default"
        env_special_key = _get_special_key(data, "env")
        default_special_key = _get_special_key(data, "default")

        # Defaults to "$path"
        path_special_key = _get_special_key(data, "path")

        # Defaults to "$insert" and "$variable"
        insert_special_key = _get_special_key(data, "insert")
        variable_special_key = _get_special_key(data, "variable")

        # Defaults to "$none"
        none_special_key = _get_special_key(data, "none")

        if env_special_key in value:
            default_value = value.get(default_special_key)

            value = os.getenv(value[env_special_key], default_value)
        elif path_special_key in value:
            file_name = value[path_special_key]

            value = _parse_path(path, file_name)
        elif insert_special_key in value:
            insert_data = data.get(key, [])
            variable = data.get(variable_special_key)

            # Check the existing value is an array
            if not isinstance(insert_data, list):
                raise InvalidActionError(f"`insert` cannot be used for value of type: {type(data[key])}")

            # Insert the data
            index = value.get(insert_special_key, len(insert_data))
            insert_data.insert(index, value[insert_special_key])

            # Set the value to the new data
            value = insert_data
        elif none_special_key in value and value.get(none_special_key):
            value = None
    elif isinstance(value, str):
        # Handle variable substitution
        for match in re.finditer(r"\$\{\w+\}", value):
            data_key = value[match.start() : match.end()][2:-1]

            if variable := data.get(data_key):
                if isinstance(variable, Path):
                    path_str = _combine_bookends(value, match, variable)

                    value = Path(path_str)
                elif callable(variable):
                    value = variable
                elif isinstance(variable, int):
                    value = _combine_bookends(value, match, variable)

                    try:
                        value = int(value)
                    except Exception:  # noqa: S110
                        pass
                elif isinstance(variable, float):
                    value = _combine_bookends(value, match, variable)

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


@typechecked
def _parse_path(path: Path, file_name: str) -> Path:
    """Parse a path string relative to a base path.

    Args:
        file_name: Relative or absolute file name.
        path: Base path to resolve file_name against.
    """

    _path = Path(path).parent if path.is_file() else path

    return (_path / file_name).resolve()


@typechecked
def _combine_bookends(original: str, match: re.Match, middle: Any) -> str:
    """Get the beginning of the original string before the match, and the
    end of the string after the match and smush the replaced value in between
    them to generate a new string.
    """

    start_idx = match.start()
    start = original[:start_idx]

    end_idx = match.end()
    ending = original[end_idx:]

    return start + str(middle) + ending


@typechecked
def _get_special_key(data: dict, key: str) -> str:
    """Gets the key for the "special". Defaults to "$" as the prefix, and "" as the suffix.

    To change in the included TOML settings, set:
    ```
    TOML_SETTINGS_SPECIAL_PREFIX = ""
    TOML_SETTINGS_SPECIAL_SUFFIX = ""
    ```
    """

    prefix = data.get("TOML_SETTINGS_SPECIAL_PREFIX", "$")
    suffix = data.get("TOML_SETTINGS_SPECIAL_SUFFIX", "")

    return f"{prefix}{key}{suffix}"
