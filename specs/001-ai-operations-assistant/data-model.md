# Data Model: Enterprise AI Operations Assistant

**Feature**: `001-ai-operations-assistant`  
**Date**: 2026-10-15  
**Context**: Modelado de entidades y esquemas de validación Pydantic v2

---

## 1. Domain Entities

### 1.1 Documento Operativo (`DocumentMetadata`)
Representa un documento ingerido en el vector store.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `doc_id` | `str` (UUID) | Sí | Identificador único del documento |
| `filename` | `str` | Sí | Nombre original del archivo |
| `file_hash` | `str` (SHA-256) | Sí | Hash para evitar duplicados en ingesta |
| `chunk_count` | `int` | Sí | Cantidad de fragmentos generados |
| `created_at` | `datetime` | Sí | Fecha y hora de procesamiento (UTC) |
| `category` | `str` | No | Categoría operativa (ej. `infraestructura`, `procedimiento`, `seguridad`) |

### 1.2 Fragmento de Contexto (`DocumentChunk`)
Segmento individual recuperado en el pipeline RAG.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `chunk_id` | `str` | Sí | Identificador del fragmento (`{doc_id}_{index}`) |
| `content` | `str` | Sí | Texto del fragmento |
| `source` | `str` | Sí | Nombre del documento de origen |
| `page_or_section`| `str` | No | Localizador dentro del documento |
| `score` | `float` | No | Puntuación de similitud o distancia |

### 1.3 Solicitud Operativa Sintética (`OperationalRequest`)
Registro para consultas de la herramienta `consultar_estado_solicitud`.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `request_id` | `str` | Sí | ID estructurado (ej. `REQ-1001`, `REQ-1002`) |
| `title` | `str` | Sí | Título descriptivo de la solicitud |
| `status` | `str` | Sí | `PENDIENTE`, `EN_PROGRESO`, `APROBADO`, `RECHAZADO`, `COMPLETADO` |
| `category` | `str` | Sí | Tipo de solicitud (`ACCESO`, `MODERNIZACION`, `INFRAESTRUCTURA`, `BUG`) |
| `requester` | `str` | Sí | Área o usuario solicitante |
| `created_at` | `str` | Sí | Fecha de radicación |
| `details` | `str` | No | Notas técnicas adicionales |

### 1.4 Dictamen de Priorización (`PriorityAssessment`)
Salida de la herramienta `clasificar_y_recomendar_solicitud`.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `priority` | `str` | Sí | Nivel de prioridad: `ALTA`, `MEDIA`, `BAJA` (según reglas de severidad de FR-006) |
| `estimated_effort_days` | `int` | Sí | Esfuerzo estimado en días hábiles (según reglas) |
| `rule_applied` | `str` | Sí | Regla de severidad activada |
| `justification` | `str` | Sí | Argumentación técnica de la clasificación |

### 1.5 Registro Histórico de Interacción (`InteractionLogRecord`)
Registro inmutable para trazabilidad y auditoría (`FR-008`, `FR-009`).

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :---: | :--- |
| `interaction_id` | `str` (UUID) | Sí | Identificador único de la interacción |
| `timestamp` | `datetime` | Sí | Marca de tiempo UTC |
| `query` | `str` | Sí | Pregunta original del usuario |
| `answer` | `str` | Sí | Respuesta generada por el asistente |
| `sources` | `List[dict]` | Sí | Lista de fuentes referenciadas (`source`, `chunk_id`) |
| `tools_used` | `List[dict]` | Sí | Lista de herramientas ejecutadas con sus parámetros y resultados |
| `duration_ms` | `float` | Sí | Latencia total de la operación |
| `status` | `str` | Sí | `SUCCESS`, `ABSTENTION`, `ERROR` |

---

## 2. API Request & Response Schemas (Pydantic v2)

```python
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Request / Response para /api/v1/query
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000, description="Consulta del usuario")
    session_id: Optional[str] = Field(None, description="ID opcional para correlación de sesión")

class SourceReference(BaseModel):
    source: str
    chunk_id: Optional[str] = None
    snippet: Optional[str] = None

class ToolExecutionResult(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    output: Any

class QueryResponse(BaseModel):
    interaction_id: str
    query: str
    answer: str
    sources: List[SourceReference] = []
    tools_used: List[ToolExecutionResult] = []
    duration_ms: float
    status: str  # SUCCESS, ABSTAINED, ERROR

# Request / Response para /api/v1/documents
class DocumentIngestResponse(BaseModel):
    doc_id: str
    filename: str
    chunks_created: int
    message: str
    created_at: datetime

# Request / Response para /api/v1/history
class HistoryResponse(BaseModel):
    total: int
    interactions: List[Dict[str, Any]]

# Request / Response para /api/v1/health
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    vectorstore_status: str
```

---

## 3. Physical Storage Schemas

### 3.1 Amazon DynamoDB (`enterprise-ai-assistant-history-production`)
Tabla NoSQL serverless de pago por solicitud para auditoría inmutable en producción.

- **Partition Key (HASH)**: `interaction_id` (`String` / UUID v4)
- **Sort Key (RANGE)**: `timestamp` (`String` / ISO-8601 UTC)
- **Atributos**:
  - `session_id` (`String`): Identificador correlacional de sesión.
  - `query` (`String`): Pregunta formulada.
  - `answer` (`String`): Respuesta estructurada entregada.
  - `sources` (`List[Map]`): Lista de fuentes documentales citadas.
  - `tools_used` (`List[Map]`): Detalle de herramientas ejecutadas con sus entradas y salidas.
  - `duration_ms` (`Number` / `Decimal`): Latencia total del procesamiento.
  - `status` (`String`): `SUCCESS`, `ABSTAINED`, `ERROR`.

### 3.2 Amazon S3 Storage Layout (`rag-docs-production-*`)
Bucket de almacenamiento inmutable cifrado con SSE-AES256.

```text
rag-docs-production-<id>/
├── documents/
│   ├── politica_seguridad_accesos.md
│   ├── procedimiento_actualizacion_db.md
│   ├── manual_despliegues_canary.md
│   └── protocolo_rotacion_claves_kms.md
└── vectorstore/
    └── dynamic_chunks.json  (Vectores de 1536 dimensiones generados con Bedrock Titan)
```

### 3.3 SQLite Local (`./data/history.db`)
Almacenamiento relacional local para desarrollo offline sin credenciales cloud.

```sql
CREATE TABLE IF NOT EXISTS interaction_history (
    interaction_id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    tools_used_json TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON interaction_history (timestamp DESC);
```

