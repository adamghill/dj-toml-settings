# dj-toml-settings ⚙️

> Load Django settings from a TOML file

`dj-toml-settings` reads settings from a TOML file. By default, both `pyproject.toml` and `django.toml` files are parsed for settings in the `[tool.django]` namespace.

```toml
[tool.django]

# Paths are relative to the TOML file (unless they are absolute)
BASE_DIR = { "$path" = "." }
STATIC_ROOT = { "$path" = "staticfiles" }

# This sets the key based on the environment variable
SECRET_KEY = { "$env" = "SECRET_KEY" }

# This sets the key based on the environment variable, but has a fallback
ADMIN_URL_PATH = { "$env" = "ADMIN_URL_PATH", "$default"="admin" }

# Booleans, arrays, tables (dictionaries), integers, strings, floats, dates are all supported in TOML
DEBUG = true
ALLOWED_HOSTS = [
  "127.0.0.1",
]

# Values can be casted to a bool, int, str, float, decimal, datetime, date, time, timedelta, url
SITE_ID = { "$value" = "1", "$type" = "int" }

# This is an implicit dictionary and equivalent to `COLTRANE = { TITLE = "Example blog" }`
[tool.django.COLTRANE]
TITLE = "Example blog"

# Any name can be used under `apps` for organizational purposes
[tool.django.apps.tailwind-cli]
TAILWIND_CLI_USE_DAISY_UI = true
TAILWIND_CLI_SRC_CSS = ".django_tailwind_cli/source.css"

# These settings are included when the `ENVIRONMENT` environment variable is "development"
[tool.django.envs.development]
ALLOWED_HOSTS = { "$insert" = "example.localhost" }

# These settings are included when the `ENVIRONMENT` environment variable is "production"
[tool.django.envs.production]
DEBUG = false
ALLOWED_HOSTS = { "$insert" = "example.com" }
```

## Features 🤩

### Variables

Use `${SOME_VARIABLE_NAME}` to use an existing setting as a value.

```toml
[tool.django]
GOOD_IPS = ["127.0.0.1"]
ALLOWED_HOSTS = "${GOOD_IPS}"  # this needs to be quoted to be valid TOML, but will be converted into a `list`
```

### Apps

`[tool.django.apps.{ANY_NAME_HERE}]` sections of the TOML file can be used to group settings together. They can be named anything. They will override any settings in `[tool.django]`.

```toml
[tool.django.apps.tailwind-cli]
TAILWIND_CLI_USE_DAISY_UI = true
TAILWIND_CLI_SRC_CSS = ".django_tailwind_cli/source.css"
```

### Environments

The `[tool.django.envs.{ENVIRONMENT_NAME}]` section of the TOML file will be used when `{ENVIRONMENT_NAME}` is set to the `ENVIRONMENT` environment variable. For example, `ENVIRONMENT=production python manage.py runserver` will load all settings in the `[tool.django.envs.production]` section. There settings will override any settings in `[tool.django.apps.*]` or `[tool.django]`.

```toml
[tool.django]
ALLOWED_HOSTS = ["127.0.0.1"]

[tool.django.envs.development]
ALLOWED_HOSTS = ["example.localhost"]

[tool.django.envs.production]
ALLOWED_HOSTS = ["example.com"]
```

## Special operations 😎

By default, special operations are denoted by an [`inline table`](https://toml.io/en/v1.0.0#inline-table), (aka a `dictionary`) with a key that starts with a `$`, e.g. `{ "$value" = "1" }`.

The prefix and suffix that denotes a special operation can be configured with `TOML_SETTINGS_SPECIAL_PREFIX` or `TOML_SETTINGS_SPECIAL_SUFFIX` in `[tool.django]`.

```toml
[tool.django]
TOML_SETTINGS_SPECIAL_PREFIX = "&"
TOML_SETTINGS_SPECIAL_SUFFIX = "*"
BASE_DIR = { "&path*" = "." }
```

### Path

Converts a string to a `Path` object by using a `$path` key. Handles relative paths based on the location of the parsed TOML file.

```toml
[tool.django]
BASE_DIR = { "$path" = "." }
PROJECT_DIR = { "$path" = "./your_project_folder" }
REPOSITORY_DIR = { "$path" = "./.." }
```

### Environment Variable

Retrieve variables from the environment by using an `$env` key. Specify an optional `$default` key for a fallback value.

```toml
[tool.django]
EMAIL_HOST_PASSWORD = { "$env" = "SECRET_PASSWORD" }
SECRET_KEY = { "$env" = "SECRET_KEY", "$default" = "this-is-a-secret" }
```

### Arrays

Add items to an array by using the `$insert` key.

```toml
[tool.django]
ALLOWED_HOSTS = { "$insert" = "127.0.0.1" }
```

Specify the index of the new item with the `$index` key.

```toml
[tool.django]
ALLOWED_HOSTS = { "$insert" = "127.0.0.1", "$index" = 0 }
```

### None

Specify `None` for a variable with a `$none` key. The value must be truthy, i.e. `true` or 1 (even though the value won't get used).

```toml
[tool.django]
EMAIL_HOST_PASSWORD = { "$none" = 1 }
```

### Value

Specifies a value for a variable.

```toml
[tool.django]
SITE_ID = { "$value" = 1 }
```

### Type

Casts the value to a particular type. Supported types: `bool`, `int`, `str`, `float`, `decimal`, `datetime`, `date`, `time`, `timedelta`, `url`. Especially helpful for values that come from environment variables which are usually read in as strings.

`$type` can be used as an additional operator with any other operator.

```toml
[tool.django]
SITE_ID = { "$env" = "SITE_ID", $type = "int" }
```

```toml
[tool.django]
SITE_ID = { "$value" = "1", $type = "int" }
```

## Example Integrations 💚

### Django

This will override any variables defined in `settings.py` with settings from the TOML files.

```python
# settings.py
from pathlib import Path
from dj_toml_settings import configure_toml_settings

BASE_DIR = Path(__file__).resolve().parent.parent
...

configure_toml_settings(base_dir=BASE_DIR, data=globals())
```

### [nanodjango](https://nanodjango.readthedocs.io) 

```python
# app.py
from pathlib import Path
from dj_toml_settings import get_toml_settings

base_dir = Path(__file__).resolve().parent
app = Django(**get_toml_settings(base_dir=base_dir))

...
```

### [coltrane](https://coltrane.adamghill.com)

```python
# app.py
from pathlib import Path
from django.core.management import execute_from_command_line
from dj_toml_settings import get_toml_settings
from coltrane import initialize

base_dir = Path(__file__).resolve().parent.parent
wsgi = initialize(**get_toml_settings(base_dir=base_dir))

if __name__ == "__main__":
    execute_from_command_line()

...
```

## Precedence 🔻

This is the order that files and sections are parsed (by default). The later sections override the previous settings.

1. `pyproject.toml` -> `[tool.django]`
2. `pyproject.toml` -> `[tool.django.apps.*]`
3. `pyproject.toml` -> `[tool.django.envs.*]` that match `ENVIRONMENT` environment variable
4. `django.toml` -> `[tool.django]`
5. `django.toml` -> `[tool.django.apps.*]`
6. `django.toml` -> `[tool.django.envs.*]` that match `ENVIRONMENT` environment variable

## Specify a TOML file 🤓

```python
from pathlib import Path
from dj_toml_settings import get_toml_settings

base_dir = Path(__file__).resolve().parent
toml_settings = get_toml_settings(base_dir=base_dir, toml_settings_files=["custom-settings.toml"])
...
```

## Test 🧪

- `uv install pip install -e .[dev]`
- `just test`

## Inspiration 😍

- [django-pyproject](https://github.com/Ceterai/django-pyproject)
- [django-settings-toml](https://github.com/maxking/django-settings-toml)
