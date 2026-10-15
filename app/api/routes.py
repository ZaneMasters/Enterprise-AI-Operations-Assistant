"""Rutas y controladores de la API REST de FastAPI."""

import os
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.api.schemas import (
    DocumentIngestResponse,
    HealthResponse,
    HistoryResponse,
    QueryRequest,
    QueryResponse,
)
from app.agent.executor import agent_executor
from app.core.config import get_settings
from app.core.logger import logger
from app.rag.ingest import ingest_service
from app.storage.history_db import history_repo

router = APIRouter()


# --- Endpoint de Salud (RF-06, User Story 5) ---

@router.get("/health", response_model=HealthResponse, tags=["Health"])
@router.get("/api/v1/health", response_model=HealthResponse, include_in_schema=False)
async def health_check() -> HealthResponse:
    """Verifica la disponibilidad del servicio y del vector store sin exponer credenciales."""
    try:
        count = ingest_service.collection.count()
        vs_status = f"ready ({count} chunks)"
    except Exception as e:
        logger.error(f"Error verificando vector store: {e}")
        vs_status = "degraded"

    return HealthResponse(
        status="ok",
        version=get_settings().APP_VERSION,
        vectorstore_status=vs_status
    )


# --- Endpoint de Consulta / Chat RAG y Agente (RF-01, User Story 1 & 3) ---

@router.post("/chat", response_model=QueryResponse, tags=["Chat"])
@router.post("/api/v1/query", response_model=QueryResponse, include_in_schema=False)
async def chat_endpoint(payload: QueryRequest) -> QueryResponse:
    """
    Recibe la consulta del usuario, ejecuta RAG y herramientas controladas,
    y devuelve una respuesta fundamentada con citas de fuentes o abstención formal.
    """
    try:
        response = await agent_executor.execute(
            query=payload.query,
            session_id=payload.session_id
        )
        return response
    except Exception as e:
        logger.error(f"Error inesperado en chat_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al procesar la solicitud en el asistente."
        )


# --- Endpoint de Ingesta Documental (RF-02, User Story 2) ---

@router.post("/documents", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED, tags=["Documents"])
@router.post("/api/v1/documents", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def ingest_document_endpoint(
    file: UploadFile = File(...),
    category: Optional[str] = Form("general")
) -> DocumentIngestResponse:
    """
    Recibe archivos en formato .md, .txt o .pdf, extrae su texto,
    lo divide en fragmentos e indexa en ChromaDB para búsquedas semánticas.
    """
    filename = file.filename or "unnamed_document"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".md", ".txt", ".pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no admitido '{ext}'. Solo se admiten archivos .md, .txt y .pdf."
        )

    # Leer archivo
    try:
        content_bytes = await file.read()
        if not content_bytes or len(content_bytes.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo proporcionado está vacío."
            )

        # Si es PDF, guardarlo temporalmente para que pypdf lo lea
        if ext == ".pdf":
            temp_path = f"./data/temp_{filename}"
            with open(temp_path, "wb") as f:
                f.write(content_bytes)
            try:
                text = ingest_service.extract_text_from_file(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            text = content_bytes.decode("utf-8", errors="replace")

        doc_id, total_chunks = ingest_service.ingest_document(
            filename=filename,
            content=text,
            category=category or "general"
        )

        return DocumentIngestResponse(
            doc_id=doc_id,
            filename=filename,
            chunks_created=total_chunks,
            message=f"Documento '{filename}' procesado e indexado exitosamente ({total_chunks} fragmentos)."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando documento '{filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el archivo: {str(e)}"
        )


# --- Endpoint de Historial y Auditoría (RF-05, User Story 4) ---

@router.get("/history", response_model=HistoryResponse, tags=["History"])
@router.get("/api/v1/history", response_model=HistoryResponse, include_in_schema=False)
async def get_history_endpoint(
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad máxima de registros a retornar (1-100)")
) -> HistoryResponse:
    """
    Consulta el registro histórico inmutable de interacciones,
    ordenado de la más reciente a la más antigua sin exponer información sensible.
    """
    try:
        records = await history_repo.get_history(limit=limit)
        return HistoryResponse(
            total=len(records),
            interactions=records
        )
    except Exception as e:
        logger.error(f"Error al recuperar historial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el historial de interacciones."
        )
