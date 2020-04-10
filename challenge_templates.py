from abc import ABC, abstractmethod
from typing import Sequence, Tuple, Mapping, Type

from common_types import TemplateConfig, ConfigurationError, Challenge, CaptchaError, DataTables, RNG


#################################################################
# Framework
#################################################################
class UnknownTemplate(ConfigurationError):
    pass


class BadTemplateParameters(ConfigurationError):
    pass


class ChallengeTemplate(ABC):
    """Abstract base class for all challenge types."""
    @classmethod
    def get_config_name(cls):
        """Allow derived classes to override the way they are referenced in the config files.
           Use the class name as default."""
        return getattr(cls, 'config_name', cls.__name__)

    @abstractmethod
    def generate_challenge(self, data: DataTables, rng: RNG) -> Tuple[Challenge, str]:
        """Generate and return a challenge and its correct answer."""
        pass


def get_class_by_name_mapping() -> Mapping[str, Type[ChallengeTemplate]]:
    class_by_name = {}
    for cls in ChallengeTemplate.__subclasses__():
        name = cls.get_config_name()
        if name in class_by_name:
            raise CaptchaError(f'Config name {name} used by both {class_by_name[name].__name__} and {cls.__name__}')
        class_by_name[name] = cls
    return class_by_name


def instantiate_templates(configs: Sequence[TemplateConfig]) -> Sequence[ChallengeTemplate]:
    cls_by_name = get_class_by_name_mapping()
    templates = []
    for name, params in configs:
        try:
            cls = cls_by_name[name]
        except KeyError:
            raise UnknownTemplate(name)
        try:
            # This call may do additional type checks and raise BadTemplateParameters directly,
            # but we must catch wrong number or names of parameters here.
            t = cls(**params)
        except TypeError as ex:
            raise BadTemplateParameters(f'Wrong parameters passed to template {name}: {ex}')
        templates.append(t)
    return templates


#################################################################
# Concrete template types
#################################################################
class BarTemplate(ChallengeTemplate):
    # TODO: Generalize to min / max / random sample of rows (currently only max).
    """Show several values with their associated labels as a bar chart. Ask for the label of the highest value.

    Example Config (usually as JSON string):
    ["bar", {
      "question": "These {n} cities had the most reported symptoms yesterday. Which city reported the most symptoms?",
      "table": "report_counts",
      "labels": "city_name",
      "values": "num_symptoms",
      "n": 3
    }]
    """
    config_name = 'bar'

    def __init__(self, question: str, table: str, labels: str, values: str, n: int = 3):
        self.question = question.format(n=n)
        self.table_name = table
        self.label_column = labels
        self.value_column = values
        self.n = n

    def generate_challenge(self, data: DataTables, rng: RNG) -> Tuple[Challenge, str]:
        # TODO: generalize to not only max.
        table = data[self.table_name]
        subset = table.nlargest(self.n, self.value_column)
        subset = subset[[self.label_column, self.value_column]].to_numpy()
        correct_answer = subset[0][0]
        rng.shuffle(subset)
        possible_answers = [x[0] for x in subset]
        chart = b'blerg'
        challenge = Challenge(self.question, chart, possible_answers)
        return challenge, correct_answer
