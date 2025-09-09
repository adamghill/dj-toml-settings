from datetime import date, datetime, time, timedelta
from decimal import Decimal
from os import getcwd
from pathlib import Path
from urllib.parse import ParseResult

import pytest

from dj_toml_settings.value_parsers.dict_parsers import TypeParser


def test_bool():
    parser = TypeParser(data={}, value={"$type": "bool"})

    # Test string conversions
    assert parser.parse("true") is True
    assert parser.parse("True") is True
    assert parser.parse("false") is False
    assert parser.parse("False") is False

    # Test integer conversions
    assert parser.parse(1) is True
    assert parser.parse(0) is False

    # Test already boolean
    assert parser.parse(True) is True
    assert parser.parse(False) is False

    with pytest.raises(ValueError) as e:
        assert parser.parse(1.1)

    assert "ValueError: Failed to convert 1.1 to bool: Type must be a string or int, got float" in e.exconly()


def test_int():
    parser = TypeParser(data={}, value={"$type": "int"})

    # Test string to int
    assert parser.parse("42") == 42
    assert parser.parse("-10") == -10

    # Test float to int (should truncate)
    assert parser.parse(3.14) == 3

    # Test already int
    assert parser.parse(100) == 100


def test_str():
    parser = TypeParser(data={}, value={"$type": "str"})

    # Test various types to string
    assert parser.parse(42) == "42"
    assert parser.parse(3.14) == "3.14"
    assert parser.parse(True) == "True"
    assert parser.parse(None) == "None"
    assert parser.parse("hello") == "hello"


def test_float():
    parser = TypeParser(data={}, value={"$type": "float"})

    # Test string to float
    assert parser.parse("3.14") == 3.14
    assert parser.parse("-1.5") == -1.5

    # Test int to float
    assert parser.parse(42) == 42.0

    # Test already float
    assert parser.parse(3.14) == 3.14


def test_decimal():
    parser = TypeParser(data={}, value={"$type": "decimal"})

    # Test string to Decimal
    assert parser.parse("3.14") == Decimal("3.14")
    assert parser.parse("-1.5") == Decimal("-1.5")

    # Test int to Decimal
    assert parser.parse(42) == Decimal(42)

    # Test float to Decimal (note: float imprecision might occur)
    assert float(parser.parse(3.14)) == 3.14


def test_path():
    expected = getcwd()

    parser = TypeParser(data={}, value={"$type": "path"})
    actual = parser.parse(".")

    assert isinstance(actual, Path)
    assert expected == str(actual)

    with pytest.raises(ValueError) as e:
        parser.parse(1)

    assert "ValueError: Failed to convert 1 to path: expected str, bytes or os.PathLike object, not int" in e.exconly()


def test_datetime():
    parser = TypeParser(data={}, value={"$type": "datetime"})

    actual = parser.parse("2023-01-01 12:00:00")
    assert isinstance(actual, datetime)
    assert actual.year == 2023
    assert actual.month == 1
    assert actual.day == 1
    assert actual.hour == 12


def test_datetime_invalid():
    parser = TypeParser(data={}, value={"$type": "datetime"})

    with pytest.raises(ValueError) as e:
        parser.parse("abcd")

    assert "Failed to convert 'abcd' to datetime" in e.exconly()


def test_date():
    parser = TypeParser(data={}, value={"$type": "date"})

    actual = parser.parse("2023-01-01")

    assert isinstance(actual, date)
    assert actual.year == 2023
    assert actual.month == 1
    assert actual.day == 1


def test_time():
    parser = TypeParser(data={}, value={"$type": "time"})

    actual = parser.parse("12:30:45")

    assert isinstance(actual, time)
    assert actual.hour == 12
    assert actual.minute == 30
    assert actual.second == 45


def test_timedelta():
    parser = TypeParser(data={}, value={"$type": "timedelta"})

    # Test numeric values (treated as seconds)
    assert parser.parse(60) == timedelta(seconds=60)
    assert parser.parse(90.5) == timedelta(seconds=90.5)

    # Test string formats
    assert parser.parse("30s") == timedelta(seconds=30)
    assert parser.parse("2m") == timedelta(minutes=2)
    assert parser.parse("1.5h") == timedelta(hours=1.5)
    assert parser.parse("2d") == timedelta(days=2)
    assert parser.parse("1w") == timedelta(weeks=1)

    assert parser.parse("1w 2d 3h 4m 5s 6ms 7u") == timedelta(
        weeks=1, days=2, hours=3, minutes=4, seconds=5, milliseconds=6, microseconds=7
    )

    assert parser.parse("1w2d") == timedelta(weeks=1, days=2)

    with pytest.raises(ValueError) as e:
        parser.parse({})

    assert "ValueError: Failed to convert {} to timedelta: Unsupported type for timedelta: dict" in e.exconly()

    with pytest.raises(ValueError) as e:
        parser.parse("abcd")

    assert "ValueError: Failed to convert 'abcd' to timedelta: Invalid timedelta format: abcd" in e.exconly()

    with pytest.raises(ValueError) as e:
        parser.parse("4z")

    assert "alueError: Failed to convert '4z' to timedelta: Invalid timedelta format: 4z" in e.exconly()


def test_url():
    parser = TypeParser(data={}, value={"$type": "url"})

    actual = parser.parse("https://example.com/path?query=1")

    assert isinstance(actual, ParseResult)
    assert actual.scheme == "https"
    assert actual.netloc == "example.com"
    assert actual.path == "/path"
    assert actual.query == "query=1"


def test_invalid_type():
    parser = TypeParser(data={}, value={"$type": "invalid_type"})

    with pytest.raises(ValueError) as e:
        parser.parse("some value")

    assert "Unsupported type: invalid_type" in e.exconly()


def test_invalid_type_type():
    parser = TypeParser(data={}, value={"$type": 1})

    with pytest.raises(ValueError) as e:
        parser.parse("some value")

    assert "Type must be a string, got int" in e.exconly()
