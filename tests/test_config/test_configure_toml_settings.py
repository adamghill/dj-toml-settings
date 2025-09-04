from types import ModuleType

from dj_toml_settings.config import configure_toml_settings


def test(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "dj_toml_settings.config.get_toml_settings",
        lambda *_: {},
    )

    expected = {}

    actual = {}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_toml_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "dj_toml_settings.config.get_toml_settings",
        lambda *_: {"ALLOWED_HOSTS": ["127.0.0.1"]},
    )

    expected = {"ALLOWED_HOSTS": ["127.0.0.1"]}

    actual = {}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_existing_settings(tmp_path):
    expected = {"DEBUG": True, "ALLOWED_HOSTS": ["127.0.0.1"]}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
""")

    actual = {"ALLOWED_HOSTS": ["127.0.0.1"]}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_empty_existing_settings_empty(tmp_path):
    expected = {"DEBUG": True}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
""")

    actual = {}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_override_existing_settings(tmp_path):
    expected = {"DEBUG": True}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
DEBUG = true
""")

    actual = {"DEBUG": False}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_override_toml_settings(tmp_path):
    expected = {"ALLOWED_HOSTS": ["127.0.0.3"]}

    (tmp_path / "pyproject.toml").write_text("""
[tool.django]
ALLOWED_HOSTS = ["127.0.0.2"]
""")

    (tmp_path / "django.toml").write_text("""
[tool.django]
ALLOWED_HOSTS = ["127.0.0.3"]
""")

    actual = {"ALLOWED_HOSTS": ["127.0.0.1"]}
    configure_toml_settings(base_dir=tmp_path, data=actual)

    assert expected == actual


def test_configure_toml_settings_without_data_parameter(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "dj_toml_settings.config.get_toml_settings",
        lambda *_: {
            "DEBUG": True,
        },
    )

    settings_module = ModuleType("test.settings")

    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "test.settings")
    monkeypatch.setattr(
        "importlib.import_module",
        lambda *_: settings_module,
    )
    configure_toml_settings(base_dir=tmp_path)

    assert settings_module.DEBUG is True
