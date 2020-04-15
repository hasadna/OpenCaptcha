import math
import secrets
import time
from typing import Mapping, Sequence, Tuple

import Levenshtein
import pandas as pd

from common_types import RNG, InputTable, TemplateConfig, ChallengeId, Challenge, ServerContext
from challenge_templates import instantiate_templates


def _get_timestamp():
    return int(time.time())


def _generate_challenge_id() -> ChallengeId:
    return ChallengeId(secrets.token_hex(16))


class CaptchaGenerator:
    def __init__(self,
                 data: Mapping[str, InputTable],
                 template_configs: Sequence[TemplateConfig],
                 response_timeout_sec: int,
                 num_letters_per_allowed_typo: int = 5,
                 verify_config: bool = True):
        self.data = {name: pd.DataFrame.from_records(table) for name, table in data.items()}
        self.templates = instantiate_templates(template_configs)
        self.response_timeout_sec = response_timeout_sec
        self.num_letters_per_allowed_typo = num_letters_per_allowed_typo
        self._non_crypto_rng = RNG()

        # Catch configuration errors early
        if verify_config:
            for t in self.templates:
                t.generate_challenge(self.data, self._non_crypto_rng)

    def generate_challenge(self, attempt_number: int = 1) -> Tuple[ChallengeId, Challenge, ServerContext]:
        challenge_id = _generate_challenge_id()
        template = self._non_crypto_rng.choice(self.templates)
        challenge, correct_answer = template.generate_challenge(self.data, self._non_crypto_rng)
        context = ServerContext(_get_timestamp(), attempt_number, correct_answer)
        return challenge_id, challenge, context

    def verify_response(self, user_answer: str, context: ServerContext) -> bool:
        elapsed_time = _get_timestamp() - context.timestamp
        if elapsed_time > self.response_timeout_sec:
            return False

        distance = Levenshtein.distance(user_answer, context.correct_answer)
        max_distance = math.ceil(len(context.correct_answer) / self.num_letters_per_allowed_typo)
        if distance > max_distance:
            return False

        return True
