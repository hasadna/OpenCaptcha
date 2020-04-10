import dataclasses
import json
from typing import Mapping, Sequence, Tuple

import pandas as pd

from common_types import InputTable, TemplateConfig, ChallengeId, Challenge, ServerContext
from challenge_templates import instantiate_templates


class CaptchaGenerator:
    def __init__(self,
                 data: Mapping[str, InputTable],
                 template_configs: Sequence[TemplateConfig],
                 response_timeout_sec: float):
        self.data = {name: pd.DataFrame.from_records(table) for name, table in data.items()}
        self.templates = instantiate_templates(template_configs)
        self.response_timeout_sec = response_timeout_sec

    def generate_challenge(self, attempt_number: int = 1) -> Tuple[ChallengeId, Challenge, ServerContext]:
        pass

    def verify_response(self, user_answer: str, context: ServerContext) -> bool:
        pass
