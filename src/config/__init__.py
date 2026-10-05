# -*- coding: utf-8 -*-
"""配置模块"""

from .settings import Config, config
from .prompts import SystemPrompts
from .responses import RefuseResponses

__all__ = ["Config", "config", "SystemPrompts", "RefuseResponses"]
