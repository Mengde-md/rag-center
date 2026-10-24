import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, code: int, msg: str, status_code: int, data: Any = None):
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.status_code = status_code
        self.data = data


class KnowledgeBaseNotFound(AppError):
    def __init__(self) -> None:
        super().__init__(40001, "knowledge base not found", 404)


class EmbeddingError(AppError):
    def __init__(self, message: str = "embedding provider unavailable") -> None:
        super().__init__(50201, message, 502)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder({"code": exc.code, "msg": exc.msg, "data": exc.data}),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Omit raw inputs (including document content) and non-serializable validator contexts.
        errors = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"code": 42201, "msg": "request validation failed", "data": errors},
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code * 100, "msg": str(exc.detail), "data": None},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Avoid logging SQL parameters, document bodies, tokens, and raw upstream responses.
        logger.error("Unhandled request error: %s", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"code": 50000, "msg": "internal server error", "data": None},
        )
