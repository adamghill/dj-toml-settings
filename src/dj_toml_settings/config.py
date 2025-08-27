from pathlib import Path

from typeguard import typechecked

from dj_toml_settings.toml_parser import parse_file

TOML_SETTINGS_FILES = ["pyproject.toml", "django.toml"]


@typechecked
def get_toml_settings(base_dir: Path, data: dict | None = None, toml_settings_files: list | None = None) -> dict:
    """Gets the Django settings from the TOML files.

    TOML files to look in for settings:
    - pyproject.toml
    - django.toml
    """
    toml_settings_files = toml_settings_files or TOML_SETTINGS_FILES

    if data is None:
        data = {}

    for settings_file_name in toml_settings_files:
        settings_path = base_dir / settings_file_name
        if settings_path.exists():
            file_data = parse_file(settings_path, data=data.copy())
            data.update(file_data)

    return data


@typechecked
def configure_toml_settings(base_dir: Path, data: dict) -> None:
    """Configure Django settings from TOML files.

    Args:
        base_dir: Base directory to look for TOML files
        data: Dictionary to update with settings from TOML files

    Returns:
        The updated dictionary with settings from TOML files
    """

    toml_settings = get_toml_settings(base_dir, data)
    data.update(toml_settings)
