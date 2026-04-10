"""
Middleware Package

Contains middleware components for the AI application.
"""

from .error_handler import error_handler_middleware

__all__ = ['error_handler_middleware']
