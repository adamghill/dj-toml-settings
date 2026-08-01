import importlib
import logging
import os
from importlib import resources
from pathlib import Path
from types import ModuleType
from typing import Any

from typeguard import typechecked

from dj_toml_settings.toml_parser import Parser

logger = logging.getLogger(__name__)

TOML_SETTINGS_FILES = [
    "pyproject.toml",
    "django.toml",
]


def _find_toml_file(module: ModuleType) -> Path:
    """Look for either a toml file alongside the settings module, or pyproject.toml"""

    # Get the name of the module without the package
    module_name = module.__name__.rsplit(".", maxsplit=1)[0]

    # Try finding the resource as either <module_name>.toml, or django.toml
    for filename in [f"{module_name}.toml", "django.toml"]:
        if resources.is_resource(module, filename):
            p = resources.path(module, filename)
            if isinstance(p, Path):
                return p

    # Try finding pyproject.toml or django_settings.toml in parent directories
    cwd = Path.cwd()
    while cwd != cwd.parent:
        for filename in ["pyproject.toml", "django.toml"]:
            p = cwd / filename
            if p.exists():
                return p

    raise RuntimeError("Could not find any pyproject.toml or django.toml file")


@typechecked
def configure_toml_settings(
    data: dict | None = None, base_dir: Path = Path("."), toml_settings_files: list[str] | None = None
) -> None:
    """Configure Django settings from TOML files.

    Args:
        base_dir: Base directory to look for TOML files
        data: Dictionary to update with settings from TOML files

    Returns:
        The updated dictionary with settings from TOML files
    """

    toml_settings = get_toml_settings(data=data, base_dir=base_dir, toml_settings_files=toml_settings_files)

    if data is not None:
        data.update(toml_settings)
    elif django_settings_module := os.getenv("DJANGO_SETTINGS_MODULE"):
        module = importlib.import_module(django_settings_module)

        for k, v in toml_settings.items():
            setattr(module, k, v)
    else:
        raise RuntimeError("No DJANGO_SETTINGS_MODULE environment variable configured")


def get_toml_settings(
    data: dict | None = None, base_dir: Path = Path("."), toml_settings_files: list[str] | None = None
) -> dict[str, Any]:
    toml_settings_files = toml_settings_files or TOML_SETTINGS_FILES
    data = data or {}

    for settings_file_name in toml_settings_files:
        settings_path = base_dir / settings_file_name

        if settings_path.exists():
            file_data = Parser(settings_path, data=data.copy()).parse_file()
            data.update(file_data)

    return data
