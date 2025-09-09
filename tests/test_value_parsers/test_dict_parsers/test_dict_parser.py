import pytest

from dj_toml_settings.value_parsers.dict_parsers import DictParser


class FakeParser(DictParser):
    pass


class FakeParserWithKey(DictParser):
    key = "test"


def test_missing_key():
    with pytest.raises(NotImplementedError) as e:
        FakeParser({}, {})

    assert "Missing key attribute" in e.exconly()


def test_missing_parse():
    with pytest.raises(NotImplementedError) as e:
        FakeParserWithKey({}, {}).parse()

    assert "parse() not implemented" in e.exconly()
