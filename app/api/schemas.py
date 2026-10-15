"""Esquemas Pydantic v2 para validación de contratos de API y modelos de dominio."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Enums de Dominio ---

class InteractionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ABSTAINED = "ABSTAINED"
    ERROR = "ERROR"


class PriorityLevel(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class RequestStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    COMPLETADO = "COMPLETADO"


# --- Modelos de Dominio y RAG ---

class SourceReference(BaseModel):
    """Cita o referencia documental utilizada para sustentar la respuesta."""
    source: str = Field(..., description="Nombre del archivo fuente")
    chunk_id: Optional[str] = Field(None, description="Identificador del fragmento dentro del vector store")
    snippet: Optional[str] = Field(None, description="Extracto textual relevante del fragmento")
    score: Optional[float] = Field(None, description="Puntaje de similitud semántica")


class ToolExecutionResult(BaseModel):
    """Resultado de la ejecución de una herramienta del agente."""
    tool_name: str = Field(..., description="Nombre de la herramienta ejecutada")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros validados")
    output: Any = Field(..., description="Resultado obtenido de la herramienta")


class PriorityAssessment(BaseModel):
    """Resultado estructurado de la herramienta clasificar_y_recomendar_solicitud."""
    priority: PriorityLevel = Field(..., description="Nivel de severidad asignado (ALTA, MEDIA, BAJA)")
    estimated_effort_days: int = Field(..., description="Días hábiles estimados")
    rule_applied: str = Field(..., description="Regla de severidad activada")
    justification: str = Field(..., description="Justificación explicativa de la clasificación")


# --- Esquemas de API Request / Response ---

class QueryRequest(BaseModel):
    """Petición para el endpoint POST /chat o /api/v1/query."""
    query: str = Field(..., min_length=2, max_length=2000, description="Pregunta del usuario")
    session_id: Optional[str] = Field(None, description="Identificador de sesión o correlación")


class QueryResponse(BaseModel):
    """Respuesta generada por el asistente RAG."""
    interaction_id: str = Field(..., description="UUID único de la interacción")
    query: str = Field(..., description="Consulta original del usuario")
    answer: str = Field(..., description="Respuesta generada por el agente")
    sources: List[SourceReference] = Field(default_factory=list, description="Fuentes documentales citadas")
    tools_used: List[ToolExecutionResult] = Field(default_factory=list, description="Herramientas invocadas")
    duration_ms: float = Field(..., description="Duración de la operación en milisegundos")
    status: InteractionStatus = Field(..., description="Estado de finalización (SUCCESS, ABSTAINED, ERROR)")


class DocumentIngestResponse(BaseModel):
    """Respuesta tras procesar un documento en POST /documents."""
    doc_id: str = Field(..., description="UUID del documento procesado")
    filename: str = Field(..., description="Nombre del archivo cargado")
    chunks_created: int = Field(..., description="Número de fragmentos vectorizados")
    message: str = Field(..., description="Mensaje informativo del procesamiento")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HistoryResponse(BaseModel):
    """Respuesta del endpoint GET /history."""
    total: int = Field(..., description="Total de interacciones recuperadas")
    interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de interacciones históricas")


class HealthResponse(BaseModel):
    """Respuesta del endpoint GET /health."""
    status: str = Field(default="ok")
    version: str = Field(default="1.0.0")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    vectorstore_status: str = Field(default="ready")
