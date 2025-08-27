import logging
import os
import re
from pathlib import Path
from typing import Any

import toml
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
    - `env`: retrieves an environment variable; optional `default`, argument
    - `path`: converts string to a `Path`; handles relative path
    - `insert`: inserts the value to an array; optional `index` argument
    """

    if isinstance(value, dict):
        if "env" in value:
            default_value = value.get("default")

            value = os.getenv(value["env"], default_value)
        elif "path" in value:
            file_name = value["path"]

            value = parse_path(path, file_name)
        elif "insert" in value:
            insert_data = data.get(key, [])

            # Check the existing value is an array
            if not isinstance(insert_data, list):
                raise InvalidActionError(f"`insert` cannot be used for value of type: {type(data[key])}")

            # Insert the data
            index = value.get("index", len(insert_data))
            insert_data.insert(index, value["insert"])

            # Set the value to the new data
            value = insert_data
    elif isinstance(value, str):
        # Handle variable substitution
        for match in re.finditer(r"\$\{[A-Z_0-9]+\}", value):
            if variable := data.get(value[2:-1]):
                value = value.replace(match.string, variable)
            else:
                logger.warning(f"Missing variable substitution {value}")

    return {key: value}


@typechecked
def parse_path(path: Path, file_name: str) -> Path:
    """Parse a path string relative to a base path.

    Args:
        file_name: Relative or absolute file name.
        path: Base path to resolve file_name against.
    """

    _path = Path(path).parent if path.is_file() else path

    return (_path / file_name).resolve()
