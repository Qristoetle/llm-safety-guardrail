# -*- coding: utf-8 -*-
"""路由模块"""

from .chat import router as chat_router
from .logs import router as logs_router
from .health import router as health_router

__all__ = ["chat_router", "logs_router", "health_router"]
