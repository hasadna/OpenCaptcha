from abc import ABC, abstractmethod
from typing import Sequence, Mapping, Any

from common_types import TemplateConfig, ConfigurationError, Challenge


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
    def generate_challenge(self) -> Challenge:
        pass


def instantiate_templates(configs: Sequence[TemplateConfig]) -> Sequence[ChallengeTemplate]:
    cls_by_name = {cls.__name__: cls for cls in ChallengeTemplate.__subclasses__()}
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
