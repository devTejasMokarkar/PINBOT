"""
Error Handler Middleware

Global error handling for consistent API responses.
"""

import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.exceptions import AIServiceException
from src.schemas import ErrorResponse

logger = logging.getLogger(__name__)

async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """
    Global error handler middleware
    
    Catches all exceptions and returns consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
        
    except AIServiceException as e:
        # Handle known AI service exceptions
        logger.error(f"AI Service Exception: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="AI_SERVICE_ERROR",
                message=str(e)
            ).dict()
        )
        
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation Error: {e}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message=str(e)
            ).dict()
        )
        
    except KeyError as e:
        # Handle missing key errors
        logger.error(f"Key Error: {e}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="MISSING_FIELD",
                message=f"Required field missing: {e}"
            ).dict()
        )
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected Error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred"
            ).dict()
        )
