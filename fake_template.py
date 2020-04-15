from common_types import Challenge, DataTables, RNG, RenderingOptions
from challenge_templates import ChallengeTemplate


class QuestTemplate(ChallengeTemplate):
    config_name = 'quest'

    def __init__(self, quest: str = 'the holy grail', error_msg: str = None):
        self.question = 'What is your quest?'
        self.answer = f'to find {quest}'
        self.chart = b'blerg'
        self.possible_answers = [self.answer, 'Not this', 'Not that either']
        self.error_msg = error_msg

    def generate_challenge(self, data, rng, rendering_options=None):
        if self.error_msg:
            raise Exception(self.error_msg)

        challenge = Challenge(
            question=self.question,
            chart=self.chart,
            possible_answers=self.possible_answers
        )
        return challenge, self.answer
