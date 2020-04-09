from typing import Any, Mapping, Sequence
from dataclasses import dataclass
import pandas as pd


# The input types for data tables. These is used only for the API.
# Internally we convert the tables to pandas.DataFrames for convenience.
InputTableRow = Mapping[str, Any]  # column name -> value
InputTable = Sequence[InputTableRow]


class ChallengeTemplate:
    def __init__(self):
        pass


@dataclass
class Challenge:
    question: str
    chart: bytes
    possible_answers: Sequence[str]
    correct_answer_index: int

    @property
    def correct_answer(self):
        return self.possible_answers[self.correct_answer_index]


class CaptchaGenerator:
    def __init__(self,
                 data: Mapping[str, InputTable],
                 templates: Sequence[ChallengeTemplate],
                 response_timeout_sec: float):
        self.data = {name: pd.DataFrame.from_records(table) for name, table in data.items()}
        self.templates = templates
        self.response_timeout_sec = response_timeout_sec

    def generate_challenge(self) -> Challenge:
        pass

    def verify_response(self, response) -> bool:
        pass
