# -*- coding: utf-8 -*-
import io
import os

from .common_types import (
    CaptchaError, ConfigurationError,
    InputTable, TemplateConfig,
    RenderingOptions, ChallengeId, Challenge, ServerContext
)
from .captcha_generator import CaptchaGenerator
from .challenge_templates import (
    UnknownTemplate, BadTemplateParameters, ChallengeTemplate
)

VERSION_FILE = os.path.join(os.path.dirname(__file__), 'VERSION')
__version__ = io.open(VERSION_FILE, encoding='utf-8').readline().strip()
