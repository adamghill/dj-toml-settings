import logging
from pathlib import Path

import pytest

from dj_toml_settings.exceptions import InvalidActionError
from dj_toml_settings.toml_parser import parse_file


def test(tmp_path):
    expected = {"ALLOWED_HOSTS": ["127.0.0.1"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]
""")

    actual = parse_file(path)

    assert expected == actual


def test_data(tmp_path):
    expected = {"DEBUG": False, "ALLOWED_HOSTS": ["127.0.0.1"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]
""")
    data = {"DEBUG": False}

    actual = parse_file(path, data=data)

    assert expected == actual


def test_data_updated(tmp_path):
    expected = {"DEBUG": True}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
DEBUG = true
""")
    data = {"DEBUG": False}

    actual = parse_file(path, data=data)

    assert expected == actual


def test_apps(tmp_path):
    expected = {"ALLOWED_HOSTS": ["127.0.0.2"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]

[tool.django.apps.whatever]
ALLOWED_HOSTS = [
    "127.0.0.2",
]
""")

    actual = parse_file(path)

    assert expected == actual


def test_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")

    expected = {"ALLOWED_HOSTS": ["127.0.0.2"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]

[tool.django.envs.production]
ALLOWED_HOSTS = [
    "127.0.0.2",
]
""")

    actual = parse_file(path)

    assert expected == actual


def test_production_missing_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")

    expected = {"ALLOWED_HOSTS": ["127.0.0.1"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
ALLOWED_HOSTS = [
    "127.0.0.1",
]

[tool.django.envs.development]
ALLOWED_HOSTS = [
    "127.0.0.2",
]
""")

    actual = parse_file(path)

    assert expected == actual


def test_precedence(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")

    expected = {"ALLOWED_HOSTS": ["127.0.0.3"]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
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

    actual = parse_file(path)

    assert expected == actual


def test_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SOME_VAR", "blob")

    expected = {"SOMETHING": "blob"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { env = "SOME_VAR" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_env_missing(tmp_path):
    expected = {"SOMETHING": None}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { env = "SOME_VAR" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_env_default(tmp_path):
    expected = {"SOMETHING": "default"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { env = "SOME_VAR", default = "default" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_path(tmp_path):
    expected = {"SOMETHING": tmp_path / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { path = "test-file" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_relative_path(tmp_path):
    expected = {"SOMETHING": tmp_path / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { path = "./test-file" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_parent_path(tmp_path):
    expected = {"SOMETHING": tmp_path.parent / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { path = "../test-file" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_parent_path_2(tmp_path):
    expected = {"SOMETHING": tmp_path.parent / "test-file"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { path = "./../test-file" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_insert(tmp_path):
    expected = {"SOMETHING": [1, 2]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = [1]

[tool.django.apps.something]
SOMETHING = { insert = 2 }
""")

    actual = parse_file(path)

    assert expected == actual


def test_insert_missing(tmp_path):
    expected = {"SOMETHING": [1]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = { insert = 1 }
""")

    actual = parse_file(path)

    assert expected == actual


def test_insert_invalid(tmp_path):
    expected = {"SOMETHING": "blob"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = "hello"

[tool.django.apps.something]
SOMETHING = { insert = 1 }
""")

    with pytest.raises(InvalidActionError) as e:
        actual = parse_file(path)

        assert expected == actual

    assert (
        "dj_toml_settings.exceptions.InvalidActionError: `insert` cannot be used for value of type: <class 'str'>"
        == e.exconly()
    )


def test_insert_index(tmp_path):
    expected = {"SOMETHING": [1, 2]}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = [1]

[tool.django.apps.something]
SOMETHING = { insert = 2, index = 2 }
""")

    actual = parse_file(path)

    assert expected == actual


def test_dict(tmp_path):
    expected = {"SOMETHING": {"blob": "hello"}}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = [1]

[tool.django.apps.something]
SOMETHING = { blob = "hello" }
""")

    actual = parse_file(path)

    assert expected == actual


def test_variable(tmp_path):
    expected = {"SOMETHING": "hello", "SOMETHING2": "hello"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = "hello"

[tool.django.apps.something]
SOMETHING2 = "${SOMETHING}"
""")

    actual = parse_file(path)

    assert expected == actual


def test_variable_invalid(tmp_path, caplog):
    expected = {"SOMETHING": "${SOMETHING2}", "SOMETHING2": "hello"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = "${SOMETHING2}"

[tool.django.apps.something]
SOMETHING2 = "hello"
""")

    with caplog.at_level(logging.WARNING):
        actual = parse_file(path)

        assert expected == actual

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert "Missing variable substitution ${SOMETHING2}" == str(actual.msg)


def test_variable_missing(tmp_path, caplog):
    expected = {"SOMETHING": "hello", "SOMETHING2": "${SOMETHING1}"}

    path = tmp_path / "pyproject.toml"
    path.write_text("""[tool.django]
SOMETHING = "hello"

[tool.django.apps.something]
SOMETHING2 = "${SOMETHING1}"
""")

    with caplog.at_level(logging.WARNING):
        actual = parse_file(path)

        assert expected == actual

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert "Missing variable substitution ${SOMETHING1}" == str(actual.msg)


def test_invalid_toml(tmp_path, caplog):
    path = tmp_path / "pyproject.toml"
    path.write_text("[")

    expected = "Cannot parse TOML at: "

    with caplog.at_level(logging.ERROR):
        parse_file(path)

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert expected in str(actual.msg)


def test_missing_file(caplog):
    expected = "Cannot find file at: missing-file"

    with caplog.at_level(logging.WARNING):
        parse_file(Path("missing-file"))

        # Check that an error was logged
        assert len(caplog.records) == 1
        actual = caplog.records[0]

        assert expected == str(actual.msg)
