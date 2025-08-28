# Changelog

## 0.2.0

- Better support for using variables which are a `Path`.

## 0.1.0

- Load `pyproject.toml` and `django.toml` files and parse them.
- Load settings from `tool.django.apps.*` sections.
- Load settings from `tool.django.envs.*` sections if it matches `ENVIRONMENT` environment variable.
- Retrieve value from environment variable, e.g. `{ env = "ENVIRONMENT_VARIABLE_NAME" }`.
- Retrieve value from previous settings, e.g. `VARIABLE_NAME = ${PREVIOUS_VARIABLE_NAME}`.
- Parse strings into a `Path` object, e.g. `{ path = "." }`.
- Insert value into arrays, e.g. `ALLOWED_HOSTS = { insert = "127.0.0.1" }`.
- Integrations for Django, `nanodjango`, `coltrane`.
