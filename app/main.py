"""Fábrica de la aplicación FastAPI, middlewares de correlación y manejadores de error."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logger import correlation_id_ctx, logger
from app.storage.history_db import history_repo


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Ciclo de vida de la aplicación: inicialización de BD y recursos."""
    logger.info("Iniciando Enterprise AI Operations Assistant...")
    await history_repo.init_db()
    yield
    logger.info("Apagando Enterprise AI Operations Assistant...")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware que inyecta y propaga el encabezado X-Request-ID para observabilidad."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id_ctx.set(req_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


def create_app() -> FastAPI:
    """Crea y configura la instancia de FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        description=(
            "API Backend del Enterprise AI Operations Assistant: Asistente RAG con "
            "herramientas controladas, abstención estricta y trazabilidad para operaciones TI."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Middlewares
    app.add_middleware(CorrelationIdMiddleware)

    # Handlers globales de excepción seguros (Principio V - Cero fugas de stack trace)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = correlation_id_ctx.get() or "N/A"
        logger.warning(f"Error de validación de solicitud ({req_id}): {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Los parámetros de la solicitud no cumplen con el esquema requerido.",
                "errors": exc.errors(),
                "request_id": req_id
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        req_id = correlation_id_ctx.get() or "N/A"
        logger.error(f"Excepción no controlada ({req_id}): {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Se produjo un error interno en el servidor. Por favor contacte al administrador.",
                "error_code": "INTERNAL_SERVER_ERROR",
                "request_id": req_id
            }
        )

    # Rutas
    app.include_router(router)

    return app


app = create_app()

# Handler para AWS Lambda serverless (Function URL y API Gateway)
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None
