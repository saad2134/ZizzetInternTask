from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class AppException(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class TenantNotFoundError(AppException):
    def __init__(self, tenant_id: str):
        super().__init__(
            message=f"Tenant '{tenant_id}' not found or access denied.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class TenantMismatchError(AppException):
    def __init__(self, requested_tenant: str, target_tenant: str):
        super().__init__(
            message=f"Tenant mismatch: Current tenant '{requested_tenant}' cannot access resources belonging to tenant '{target_tenant}'.",
            status_code=status.HTTP_403_FORBIDDEN
        )


class LeadNotFoundError(AppException):
    def __init__(self, lead_id: str, tenant_id: Optional[str] = None):
        msg = f"Lead '{lead_id}' not found."
        if tenant_id:
            msg = f"Lead '{lead_id}' not found for tenant '{tenant_id}'."
        super().__init__(
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND
        )


class AnalysisNotFoundError(AppException):
    def __init__(self, lead_id: str, tenant_id: Optional[str] = None):
        msg = f"No analysis found for lead '{lead_id}'."
        if tenant_id:
            msg = f"No analysis found for lead '{lead_id}' under tenant '{tenant_id}'."
        super().__init__(
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND
        )


class OptOutError(AppException):
    def __init__(self, lead_id: str):
        super().__init__(
            message=f"Lead '{lead_id}' has opted out (do_not_contact=true). Cannot send follow-up message.",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class LLMGenerationError(AppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"LLM generation failed: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


class WebhookJobNotFoundError(AppException):
    def __init__(self, job_id: str):
        super().__init__(
            message=f"Webhook job '{job_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        f"Handled application exception: {exc.message}",
        extra={"status_code": exc.status_code, "details": exc.details, "path": request.url.path}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"Unhandled server error at {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred during processing. Please check server logs.",
                "details": str(exc) if request.app.debug else None
            }
        }
    )
