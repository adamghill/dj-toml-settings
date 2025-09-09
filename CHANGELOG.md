# Changelog

## 0.5.0-dev

- Move from `toml` to `tomli` for TOML parsing to allow using `tomllib` in standard library for Python > 3.11.

### Breaking changes

- Remove custom prefix or suffixes for special operators. Everything should start with "$" to reduce code and unnecessary complications.

## 0.4.0

- Add `$value` operator.
- Add `$type` operator with support for `bool`, `int`, `str`, `float`, `decimal`, `datetime`, `date`, `time`, `timedelta`, `url`.

## 0.3.1

- Fix `$index`.

## 0.3.0

- Handle `datetime`, `int`, `float`, `list`, `dict`, `datetime`, and `Callable` as variables.
- Handle appending to a variable for `Path`.
- Add `$none` special operator.

### Breaking changes

- Start special operations with "$" to reduce key conflicts. Can be configured as "" to replicate 0.2.0.

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
