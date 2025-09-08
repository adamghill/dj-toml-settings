import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser as dateparser
from typeguard import typechecked

logger = logging.getLogger(__name__)


class VariableParser:
    data: dict
    value: str

    def __init__(self, data: dict, value: str):
        self.data = data
        self.value = value

    def parse(self) -> Any:
        value: Any = self.value

        for match in re.finditer(r"\$\{\w+\}", value):
            data_key = value[match.start() : match.end()][2:-1]

            if variable := self.data.get(data_key):
                if isinstance(variable, Path):
                    path_str = combine_bookends(value, match, variable)

                    value = Path(path_str)
                elif callable(variable):
                    value = variable
                elif isinstance(variable, int):
                    value = combine_bookends(value, match, variable)

                    try:
                        value = int(value)
                    except Exception:  # noqa: S110
                        pass
                elif isinstance(variable, float):
                    value = combine_bookends(value, match, variable)

                    try:
                        value = float(value)
                    except Exception:  # noqa: S110
                        pass
                elif isinstance(variable, list):
                    value = variable
                elif isinstance(variable, dict):
                    value = variable
                elif isinstance(variable, datetime):
                    value = dateparser.isoparse(str(variable))
                else:
                    value = value.replace(match.string, str(variable))
            else:
                logger.warning(f"Missing variable substitution {value}")

        return value


@typechecked
def combine_bookends(original: str, match: re.Match, middle: Any) -> str:
    """Get the beginning of the original string before the match, and the
    end of the string after the match and smush the replaced value in between
    them to generate a new string.
    """

    start_idx = match.start()
    start = original[:start_idx]

    end_idx = match.end()
    ending = original[end_idx:]

    return start + str(middle) + ending
