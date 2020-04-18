import dataclasses
import json
from typing import Sequence, Mapping, Tuple, Any, NewType

import numpy as np
import pandas as pd


#################################################################
# Exceptions
#################################################################
class CaptchaError(Exception):
    pass


class ConfigurationError(CaptchaError):
    pass


#################################################################
# Configuration
#################################################################
# The input types for data tables. These is used only for the API.
# Internally we convert the tables to pandas.DataFrames for convenience.
InputTableRow = Mapping[str, Any]  # column name -> value
InputTable = Sequence[InputTableRow]

# Input type for template configurations, which can be easily saved/loaded from
# a JSON file. Each template config is a pair of (template name, template
# parameters).
# The template parameters are specific to the type of the template being
# configured.
TemplateParams = Mapping[str, Any]
TemplateConfig = Tuple[str, TemplateParams]

#################################################################
# Internal structures
#################################################################
DataTables = Mapping[str, pd.DataFrame]
RNG = np.random.RandomState


@dataclasses.dataclass
class RenderingOptions:
    figure_size: Tuple[float, float]  # Figure size in inches

    @staticmethod
    def default_options() -> 'RenderingOptions':
        return RenderingOptions(
            figure_size=(6.4, 4.8)
        )


#################################################################
# Challenge generation
#################################################################
ChallengeId = NewType('ChallengeId', str)  # 128 bit random token


@dataclasses.dataclass
class Challenge:
    question: str
    chart: bytes
    possible_answers: Sequence[str]


@dataclasses.dataclass
class ServerContext:
    timestamp: int  # seconds since epoch
    verification_attempt_number: int
    correct_answer: str

    def to_json(self) -> str:
        d = dataclasses.asdict(self)
        return json.dumps(d)

    @staticmethod
    def from_json(s: str):
        d = json.loads(s)
        return ServerContext(**d)
