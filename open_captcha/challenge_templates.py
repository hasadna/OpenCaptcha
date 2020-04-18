from abc import ABC, abstractmethod
import io
from typing import Sequence, Tuple, Mapping, Type

import matplotlib.figure

from .common_types import (
    TemplateConfig, ConfigurationError, Challenge, CaptchaError, DataTables,
    RNG, RenderingOptions
)


#################################################################
# Framework
#################################################################
class UnknownTemplate(ConfigurationError):
    pass


class BadTemplateParameters(ConfigurationError):
    pass


class ChallengeTemplate(ABC):
    """Abstract base class for all challenge types."""
    @abstractmethod
    def generate_challenge(self,
                           data: DataTables,
                           rng: RNG,
                           rendering_options: RenderingOptions = None
                           ) -> Tuple[Challenge, str]:
        """Generate and return a challenge and its correct answer."""
        pass  # pragma: no cover


TemplateClassNameMapping = Mapping[str, Type[ChallengeTemplate]]


def get_class_by_name_mapping() -> TemplateClassNameMapping:
    class_by_name = {}
    for cls in ChallengeTemplate.__subclasses__():
        name = cls.config_name
        if name in class_by_name:
            raise CaptchaError(
                f'Config name {name} used by both '
                f'{class_by_name[name].__name__} and {cls.__name__}')
        class_by_name[name] = cls
    return class_by_name


def instantiate_one_template(cls_by_name: TemplateClassNameMapping,
                             config: TemplateConfig) -> ChallengeTemplate:
    name, params = config
    try:
        cls = cls_by_name[name]
    except KeyError:
        raise UnknownTemplate(name)
    try:
        # This call may do additional type checks and raise
        # BadTemplateParameters directly, but we must catch wrong number or
        # names of parameters here.
        template = cls(**params)
    except TypeError as ex:
        raise BadTemplateParameters(
            f'Wrong parameters passed to template {name}: {ex}')
    return template


def instantiate_templates(configs: Sequence[TemplateConfig]
                          ) -> Sequence[ChallengeTemplate]:
    cls_by_name = get_class_by_name_mapping()
    templates = [
        instantiate_one_template(cls_by_name, config)
        for config in configs
    ]
    if not templates:
        raise ConfigurationError('No templates configured')
    return templates


#################################################################
# Plotting helpers
#################################################################
def save_figure(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    return buf.getvalue()


def render_bar_chart(label_value_pairs: Sequence[Tuple[str, float]],
                     options: RenderingOptions = None) -> bytes:
    if options is None:
        options = RenderingOptions.default_options()
    labels, values = list(zip(*label_value_pairs))
    fig = matplotlib.figure.Figure(figsize=options.figure_size)
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(labels, values)
    return save_figure(fig)


#################################################################
# Concrete template types
#################################################################
class MinMaxBarTemplate(ChallengeTemplate):
    """Show several values with their associated labels as a bar chart. Ask for
     the label of the highest/lowest value.

    Example Config (usually as JSON string):
    ["bar", {
      "question": "Which of these {n} cities had the most symptoms yesterday?",
      "table": "report_counts",
      "labels": "city_name",
      "values": "num_symptoms",
      "variant": "max",
      "n": 3,
    }]
    """
    config_name = 'min-max-bar'

    def __init__(self, question: str, table: str, labels: str, values: str,
                 variant: str, n: int = 3):
        try:
            self.question = question.format(n=n)
        except Exception:
            raise ConfigurationError('The question can only contain'
                                     ' placeholders for the parameter "n"')
        self.table_name = table
        self.label_column = labels
        self.value_column = values
        if variant.lower() not in {'min', 'max'}:
            raise ConfigurationError(
                f'variant must be either "min" or "max". Got {variant}')
        self.is_max = variant.lower() == 'max'
        self.n = n

    def generate_challenge(self,
                           data: DataTables,
                           rng: RNG,
                           rendering_options: RenderingOptions = None
                           ) -> Tuple[Challenge, str]:
        table = data[self.table_name]
        choose_func = table.nlargest if self.is_max else table.nsmallest
        subset = choose_func(self.n, self.value_column)
        subset = subset[[self.label_column, self.value_column]].to_numpy()
        correct_answer = subset[0][0]
        rng.shuffle(subset)
        possible_answers = [x[0] for x in subset]
        chart = render_bar_chart(subset, rendering_options)
        challenge = Challenge(self.question, chart, possible_answers)
        return challenge, correct_answer
