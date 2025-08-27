import logging

from dj_toml_settings.config import get_toml_settings


def test(tmp_path):
    expected = {}

    actual = get_toml_settings(base_dir=tmp_path)

    assert expected == actual


def test_pyproject_only(tmp_path):
    expected = {"DEBUG": True, "SECRET_KEY": "test-secret"}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
SECRET_KEY = "test-secret"
""")

    actual = get_toml_settings(base_dir=tmp_path)

    assert expected == actual


def test_django_only(tmp_path):
    expected = {
        "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}},
        "ALLOWED_HOSTS": ["example.com"],
    }

    (tmp_path / "django.toml").write_text("""
[tool.django]
DATABASES = { default = { ENGINE = "django.db.backends.sqlite3" } }
ALLOWED_HOSTS = ["example.com"]
""")

    actual = get_toml_settings(base_dir=tmp_path)

    assert expected == actual


def test_both_files(tmp_path):
    expected = {
        "DEBUG": False,  # Should be overridden by django.toml
        "SECRET_KEY": "test-secret",
        "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}},
    }

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
SECRET_KEY = "test-secret"
""")

    (tmp_path / "django.toml").write_text("""
[tool.django]
DATABASES = {default = {ENGINE = "django.db.backends.sqlite3"}}
DEBUG = false
""")

    actual = get_toml_settings(base_dir=tmp_path)

    assert expected == actual


def test_invalid_toml(tmp_path, caplog):
    expected = {}

    (tmp_path / "pyproject.toml").write_text("this is not valid TOML")

    with caplog.at_level(logging.ERROR):
        actual = get_toml_settings(base_dir=tmp_path)

    assert expected == actual
    assert "Cannot parse TOML at: " in caplog.text


def test_empty_file(tmp_path):
    expected = {}

    (tmp_path / "pyproject.toml").write_text("")

    actual = get_toml_settings(base_dir=tmp_path)

    assert expected == actual


def test_no_files(tmp_path):
    expected = {}

    actual = get_toml_settings(base_dir=tmp_path)

    assert expected == actual
