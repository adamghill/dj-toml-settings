import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest
from dateutil import parser as dateparser

from dj_toml_settings.exceptions import InvalidActionError
from dj_toml_settings.toml_parser import Parser


def test(tmp_path):
    expected = {"ALLOWED_HOSTS": ["127.0.0.1"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_type_bool_true(tmp_path):
    expected = {"DEBUG": True}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
DEBUG = { "$value" = "True", "$type" = "bool" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_type_float(tmp_path):
    expected = {"FLOAT": float("1.5")}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
FLOAT = { "$value" = "1.5", "$type" = "float" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_data(tmp_path):
    expected = {"DEBUG": False, "ALLOWED_HOSTS": ["127.0.0.1"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]
""")
    data = {"DEBUG": False}

    actual = Parser(path, data=data).parse_file()

    assert expected == actual


def test_data_updated(tmp_path):
    expected = {"DEBUG": True}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
DEBUG = true
""")
    data = {"DEBUG": False}

    actual = Parser(path, data=data).parse_file()

    assert expected == actual


def test_apps(tmp_path):
    expected = {"ALLOWED_HOSTS": ["127.0.0.2"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]

[tool.django.apps.whatever]
ALLOWED_HOSTS = [
    "127.0.0.2",
]
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")

    expected = {"ALLOWED_HOSTS": ["127.0.0.2"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]

[tool.django.envs.production]
ALLOWED_HOSTS = [
    "127.0.0.2",
]
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_production_missing_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")

    expected = {"ALLOWED_HOSTS": ["127.0.0.1"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]

[tool.django.envs.development]
ALLOWED_HOSTS = [
    "127.0.0.2",
]
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_precedence(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")

    expected = {"ALLOWED_HOSTS": ["127.0.0.3"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]

[tool.django.apps.whatever]
ALLOWED_HOSTS = [
    "127.0.0.2",
]

[tool.django.envs.development]
ALLOWED_HOSTS = [
    "127.0.0.3",
]
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SOME_VAR", "blob")

    expected = {"SOMETHING": "blob"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$env" = "SOME_VAR" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_env_in_nested_dict(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_ENGINE", "django.db.backends.sqlite3")

    expected = {"DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}}}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django.DATABASES]
default = { ENGINE = { "$env" = "DATABASE_ENGINE", "$default" = "django.db.backends.postgresql" } }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_env_in_list(tmp_path, monkeypatch):
    monkeypatch.setenv("SOME_VAR", "blob")

    expected = {"SOMETHING": ["blob"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = [{ "$env" = "SOME_VAR"}]
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_in_list(tmp_path):
    expected = {"SOMETHING": ["blob"], "SOME_VAR": "blob"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOME_VAR = "blob"
SOMETHING = ["${SOME_VAR}"]
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_env_quoted_key(tmp_path, monkeypatch):
    monkeypatch.setenv("SOME_VAR", "blob")

    expected = {"SOMETHING": "blob"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$env" = "SOME_VAR" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_env_missing(tmp_path):
    expected = {"SOMETHING": None}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$env" = "SOME_VAR" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_env_default(tmp_path):
    expected = {"SOMETHING": "default"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$env" = "SOME_VAR", "$default" = "default" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_path(tmp_path):
    expected = {"SOMETHING": tmp_path / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$path" = "test-file" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_relative_path(tmp_path):
    expected = {"SOMETHING": tmp_path / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$path" = "./test-file" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_parent_path(tmp_path):
    expected = {"SOMETHING": tmp_path.parent / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$path" = "../test-file" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_parent_path_2(tmp_path):
    expected = {"SOMETHING": tmp_path.parent / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$path" = "./../test-file" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_insert(tmp_path):
    expected = {"SOMETHING": [1, 2]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = [1]

[tool.django.apps.something]
SOMETHING = { "$insert" = 2 }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_insert_missing(tmp_path):
    expected = {"SOMETHING": [1]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = { "$insert" = 1 }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_insert_invalid(tmp_path):
    expected = {"SOMETHING": "blob"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = "hello"

[tool.django.apps.something]
SOMETHING = { "$insert" = 1 }
""")

    with pytest.raises(InvalidActionError) as e:
        actual = Parser(path).parse_file()

        assert expected == actual

    assert (
        "dj_toml_settings.exceptions.InvalidActionError: `insert` cannot be used for value of type: <class 'str'>"
        == e.exconly()
    )


def test_insert_index(tmp_path):
    expected = {"SOMETHING": [2, 1]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = [1]

[tool.django.apps.something]
SOMETHING = { "$insert" = 2, "$index" = 0 }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_inline_table(tmp_path):
    expected = {"SOMETHING": {"blob": "hello"}}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = [1]

[tool.django.apps.something]
SOMETHING = { blob = "hello" }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_table(tmp_path):
    expected = {"SOMETHING": {"blob": "hello"}}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django.SOMETHING]
blob = "hello"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_all_dictionaries(tmp_path):
    path = tmp_path / "pyproject.toml"

    expected = {"DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}}}

    # inline table
    path.write_text("""
[tool.django]
DATABASES = { default = { ENGINE = "django.db.backends.postgresql" } }
""")

    actual = Parser(path).parse_file()
    assert expected == actual

    # table for DATABASES
    path.write_text("""
[tool.django.DATABASES]
default = { ENGINE = "django.db.backends.postgresql" }
""")

    actual = Parser(path).parse_file()
    assert expected == actual

    # table for DATABASES.default
    path.write_text("""
[tool.django.DATABASES.default]
ENGINE = "django.db.backends.postgresql"
""")

    actual = Parser(path).parse_file()
    assert expected == actual


def test_variable(tmp_path):
    expected = {"SOMETHING": "hello", "SOMETHING2": "hello"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = "hello"

[tool.django.apps.something]
SOMETHING2 = "${SOMETHING}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_callable(tmp_path):
    def some_function():
        pass

    expected = {"SOMETHING": some_function}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = "${some_function}"
""")

    actual = Parser(path, data={"some_function": some_function}).parse_file()

    assert id(expected["SOMETHING"]) == id(actual["SOMETHING"])


def test_variable_int(tmp_path):
    expected = {"INT": 123, "TEST": 1234}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
INT = 123
TEST = "${INT}4"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_int_with_string(tmp_path):
    expected = {"INT": 123, "TEST": "a123"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
INT = 123
TEST = "a${INT}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_float(tmp_path):
    expected = {"FLOAT": 123.1, "TEST": 123.14}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
FLOAT = 123.1
TEST = "${FLOAT}4"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_float_with_string(tmp_path):
    expected = {"FLOAT": 123.1, "TEST": "a123.1"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
FLOAT = 123.1
TEST = "a${FLOAT}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_array(tmp_path):
    expected = {"ARRAY": [1, 2, 3], "TEST": [1, 2, 3]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
ARRAY = [1, 2, 3]
TEST = "${ARRAY}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_dictionary(tmp_path):
    expected = {"HASH": {"a": 1}, "TEST": {"a": 1}}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
HASH = { a = 1 }
TEST = "${HASH}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_inline_table(tmp_path):
    expected = {"HASH": {"a": 1}, "TEST": {"a": 1}}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django.HASH]
a = 1

[tool.django.apps.blob]
TEST = "${HASH}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_datetime_utc(tmp_path):
    expected = {
        "DATETIME": datetime(2025, 8, 30, 7, 32, tzinfo=timezone.utc),
        "TEST": datetime(2025, 8, 30, 7, 32, tzinfo=timezone.utc),
    }

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
DATETIME = 2025-08-30T07:32:00Z

[tool.django.apps.blob]
TEST = "${DATETIME}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_datetime_tz(tmp_path):
    expected = {
        "DATETIME": dateparser.parse("2025-08-30T00:32:00-07:00"),
        "TEST": dateparser.parse("2025-08-30T00:32:00-07:00"),
    }

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
DATETIME = 2025-08-30T00:32:00-07:00

[tool.django.apps.blob]
TEST = "${DATETIME}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_none(tmp_path):
    expected = {"TEST": None}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
TEST = { "$none" = 1 }
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_invalid(tmp_path, caplog):
    expected = {"SOMETHING": "${SOMETHING2}", "SOMETHING2": "hello"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = "${SOMETHING2}"

[tool.django.apps.something]
SOMETHING2 = "hello"
""")

    with caplog.at_level(logging.WARNING):
        actual = Parser(path).parse_file()

        assert expected == actual

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert "Missing variable substitution ${SOMETHING2}" == str(actual.msg)


def test_variable_missing(tmp_path, caplog):
    expected = {"SOMETHING": "hello", "SOMETHING2": "${SOMETHING1}"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
SOMETHING = "hello"

[tool.django.apps.something]
SOMETHING2 = "${SOMETHING1}"
""")

    with caplog.at_level(logging.WARNING):
        actual = Parser(path).parse_file()

        assert expected == actual

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert "Missing variable substitution ${SOMETHING1}" == str(actual.msg)


def test_variable_start_path(tmp_path):
    expected = {"BASE_DIR": tmp_path, "STATIC_ROOT": tmp_path / "staticfiles"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
BASE_DIR = { "$path" = "." }
STATIC_ROOT = "${BASE_DIR}/staticfiles"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_variable_end_path(tmp_path):
    expected = {"BASE_DIR": Path("/something"), "STATIC_ROOT": Path("/blob/something")}

    path = tmp_path / "pyproject.toml"
    path.write_text("""
[tool.django]
BASE_DIR = { "$path" = "/something" }
STATIC_ROOT = "/blob${BASE_DIR}"
""")

    actual = Parser(path).parse_file()

    assert expected == actual


def test_invalid_toml(tmp_path, caplog):
    path = tmp_path / "pyproject.toml"
    path.write_text("[")

    expected = "Cannot parse TOML at: "

    with caplog.at_level(logging.ERROR):
        Parser(path).parse_file()

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert expected in str(actual.msg)


def test_missing_file(caplog):
    expected = "Cannot find file at: missing-file"

    with caplog.at_level(logging.WARNING):
        Parser(Path("missing-file")).parse_file()

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert expected == str(actual.msg)
