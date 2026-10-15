# Tasks: Enterprise AI Operations Assistant

**Feature**: `001-ai-operations-assistant`  
**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [data-model.md](./data-model.md), [contracts/openapi.yaml](./contracts/openapi.yaml)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del proyecto, dependencias y estructura modular base.

- [X] T001 Create core project directory layout per implementation plan (`app/api`, `app/core`, `app/rag`, `app/agent`, `app/storage`, `data/sample_docs`, `tests`, `docs`, `infra/terraform`)
- [X] T002 Initialize project dependencies in `requirements.txt` with FastAPI, Pydantic v2, Uvicorn, ChromaDB, aiosqlite, pypdf, pytest, etc.
- [X] T003 [P] Create `.env.example` and base `.gitignore` ensuring secrets and `.env` files are never tracked in version control

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura transversal que DEBE estar completa antes de implementar cualquier historia de usuario.

**⚠️ CRITICAL**: Ninguna historia de usuario puede comenzar hasta que esta fase esté finalizada.

- [X] T004 Implement application configuration and environment settings in `app/core/config.py` using `pydantic-settings`
- [X] T005 [P] Implement structured JSON logging with correlation `request_id` in `app/core/logger.py`
- [X] T006 [P] Implement input sanitization, max query length (2000 chars) validation, and prompt injection defense filters in `app/core/security.py`
- [X] T007 Implement shared Pydantic v2 domain schemas (`DocumentMetadata`, `DocumentChunk`, `OperationalRequest`, `PriorityAssessment`, `InteractionLogRecord`) in `app/api/schemas.py`
- [X] T008 Implement FastAPI application factory, global exception handlers (with no stack trace leak), and request ID middleware in `app/main.py`
- [X] T009 [P] Create synthetic operational documents in `data/sample_docs/` (`procedimiento_actualizacion_db.md`, `politica_seguridad_accesos.md`) and mock requests database in `data/requests_db.json`

**Checkpoint**: Base lista - la implementación de las historias de usuario puede comenzar.

---

## Phase 3: User Story 2 - Ingesta y Procesamiento de Documentos Operativos (Priority: P1)

**Goal**: Permitir la ingesta, validación, extracción de texto, fragmentación semántica y almacenamiento vectorial en ChromaDB para archivos `.md`, `.txt` y `.pdf` (`FR-004`, `FR-005`).

**Independent Test**: Cargar un archivo `.md`, `.txt` o `.pdf` válido mediante el endpoint o script y comprobar que se generan fragmentos con metadatos asociados (`source`, `chunk_id`) disponibles para búsqueda.

### Tests for User Story 2
- [X] T010 [P] [US2] Write unit tests for document extraction (`.md`, `.txt`, `.pdf`), chunking, and ChromaDB persistence in `tests/test_rag.py`

### Implementation for User Story 2
- [X] T011 [US2] Implement document extraction for Markdown, plain text, and PDF files, recursive text chunking, and embedding generation in `app/rag/ingest.py`
- [X] T012 [US2] Implement vector store management and similarity retriever with score thresholding in `app/rag/retriever.py`
- [X] T013 [US2] Implement endpoint `POST /documents` (and alias `POST /api/v1/documents`) in `app/api/routes.py` for file uploads and automated vector indexing
- [X] T014 [US2] Create batch sample document ingestion script in `scripts/ingest_samples.py`

**Checkpoint**: Los documentos operativos pueden ser procesados, fragmentados e indexados semánticamente de manera autónoma.

---

## Phase 4: User Story 1 - Consulta Operativa con Respuestas Fundamentadas en RAG (Priority: P1) 🎯 MVP

**Goal**: Responder consultas operativas en lenguaje natural utilizando exclusivamente fragmentos relevantes, citando fuentes explícitas y absteniéndose formalmente ante falta de datos (`FR-001`, `FR-002`, `FR-003`, `FR-013`).

**Independent Test**: Realizar una consulta respondible sobre los documentos cargados (verificando citas y fidelidad) y una consulta fuera de alcance (verificando abstención explícita).

### Tests for User Story 1
- [X] T015 [P] [US1] Write test cases for grounded answer generation, source citation, and formal abstention in `tests/test_rag.py`

### Implementation for User Story 1
- [X] T016 [US1] Implement RAG system prompt with context isolation tags (`<context_documents>`) and strict anti-hallucination rules in `app/rag/retriever.py`
- [X] T017 [US1] Implement RAG generation service that evaluates retrieval relevance score and triggers explicit abstention when no evidence exists in `app/rag/retriever.py`
- [X] T018 [US1] Implement endpoint `POST /chat` (and alias `POST /api/v1/query`) in `app/api/routes.py` and wire RAG retrieval pipeline in `app/agent/executor.py`

**Checkpoint**: El núcleo conversacional RAG con citas exactas y abstención determinista opera de extremo a extremo (MVP completado).

---

## Phase 5: User Story 3 - Invocación de Herramientas Operativas Controladas (Priority: P2)

**Goal**: Permitir que el agente ejecute al menos dos herramientas operativas con validación estricta de esquemas: consulta de solicitudes sintéticas y clasificación de prioridad en 3 niveles deterministas (`FR-006`, `FR-007`).

**Independent Test**: Consultar un ticket existente (`REQ-1001`), un ticket inexistente, y clasificar una incidencia según las reglas de negocio (Alta para caída o seguridad, Media para degradación parcial, Baja para consultas ordinarias).

### Tests for User Story 3
- [X] T019 [P] [US3] Write unit tests for Tool 1 (request query) and Tool 2 (priority classification) in `tests/test_tools.py`

### Implementation for User Story 3
- [X] T020 [P] [US3] Implement Tool 1: `consultar_estado_solicitud` with Pydantic input schema and mock lookup against `data/requests_db.json` in `app/agent/tools.py`
- [X] T021 [P] [US3] Implement Tool 2: `clasificar_y_recomendar_solicitud` evaluating the 3 severity levels (`Alta`, `Media`, `Baja`) and technical justification in `app/agent/tools.py`
- [X] T022 [US3] Implement agent executor with structured tool calling loop, parameter validation, and execution tracing in `app/agent/executor.py`

**Checkpoint**: El agente responde consultas y despacha herramientas con esquemas tipados y sin acceso arbitrario al sistema.

---

## Phase 6: User Story 4 - Consulta de Historial, Auditoría y Trazabilidad (Priority: P2)

**Goal**: Registrar cada interacción de forma inmutable y exponer el endpoint `GET /history` para auditoría y observabilidad (`FR-008`, `FR-009`).

**Independent Test**: Ejecutar consultas y verificar que `GET /history` retorna los eventos con `interaction_id`, fuentes, herramientas y duración, respetando el parámetro `limit` (por defecto 20).

### Tests for User Story 4
- [X] T023 [P] [US4] Write integration test for interaction history recording and retrieval in `tests/test_api.py`

### Implementation for User Story 4
- [X] T024 [US4] Implement SQLite persistence repository in `app/storage/history_db.py` for audit logging with descending chronological ordering
- [X] T025 [US4] Wire audit recording in `app/agent/executor.py` and implement endpoint `GET /history` (and alias `GET /api/v1/history`) with `limit` parameter (default 20, max 100) in `app/api/routes.py`

**Checkpoint**: Trazabilidad completa de auditoría e historial de consultas operativo.

---

## Phase 7: User Story 5 - Verificación de Disponibilidad y Salud del Servicio (Priority: P3)

**Goal**: Exponer endpoint de comprobación de salud `GET /health` sin exposición de secretos ni credenciales (`FR-010`).

**Independent Test**: Invocación a `GET /health` retornando 200 OK y estado del vector store sin trazas sensibles.

### Implementation for User Story 5
- [X] T026 [US5] Implement `GET /health` (and alias `GET /api/v1/health`) endpoint in `app/api/routes.py` and test in `tests/test_api.py`

**Checkpoint**: Healthcheck operativo y seguro.

---

## Phase 8: Quality Evaluation Suite (Mandatory 5 Test Cases)

**Purpose**: Ejecutar y validar los 5 casos de prueba obligatorios exigidos por la prueba técnica (`SC-007`).

- [X] T027 Write automated quality evaluation suite with the 5 mandatory scenarios in `tests/test_evaluation.py`:
  - Scenario 1: Direct answer grounded in single document with explicit source citation
  - Scenario 2: Multi-document synthesis with combined source references
  - Scenario 3: Formal abstention when information is absent from documents
  - Scenario 4: Direct prompt injection attempt mitigation
  - Scenario 5: Deterministic tool execution for ticket query and priority evaluation
- [X] T028 Execute `pytest tests/test_evaluation.py` and generate structured evaluation evidence report

---

## Phase 9: Infrastructure as Code (Terraform) & Cloud Readiness

**Purpose**: Cumplir el Principio VI y declarar la infraestructura reproducible en AWS.

- [X] T029 [P] Create modular Terraform definitions for AWS in `infra/terraform/`: `main.tf` (ECS Fargate, S3, DynamoDB, IAM), `variables.tf`, and `outputs.tf`
- [X] T030 Validate Terraform syntax and plan locally using `terraform fmt` and `terraform validate` in `infra/terraform/`

---

## Phase 10: Polish & Documentation Deliverables

**Purpose**: Elaborar los entregables finales exigidos por la prueba técnica (Principio X).

- [X] T031 [P] Create architecture diagram and component flow in `docs/architecture.md` (Mermaid format)
- [X] T032 [P] Create technical decisions document with cloud deployment guide in `docs/technical_decisions.md`
- [X] T033 [P] Document AI-assisted development log (AI-CDL) covering tools, human validations, and risk mitigations in `docs/ai_development_log.md`
- [X] T034 Create complete, production-ready `README.md` with setup, API usage examples, test commands, and future improvements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias previas - ejecutable de inmediato.
- **Foundational (Phase 2)**: Depende de Phase 1 - BLOQUEA la implementación de las historias de usuario.
- **User Story 2 - Ingesta (Phase 3)**: Depende de Phase 2. Se implementa antes de US1 para proveer documentos indexados al retriever RAG.
- **User Story 1 - Consulta RAG (Phase 4)**: Depende de Phase 2 y Phase 3 (requiere datos indexados).
- **User Story 3 - Herramientas (Phase 5)**: Depende de Phase 2. Puede desarrollarse en paralelo con US1 o secuencialmente.
- **User Story 4 - Historial (Phase 6)**: Depende de Phase 2. Registra las interacciones de US1 y US3.
- **User Story 5 - Healthcheck (Phase 7)**: Depende de Phase 2. Endpoint liviano independiente.
- **Quality Evaluation Suite (Phase 8)**: Depende de US1, US2 y US3 completadas.
- **Terraform IaC (Phase 9)**: Puede desarrollarse en paralelo una vez definida la arquitectura.
- **Polish & Documentation (Phase 10)**: Depende de todas las fases anteriores para reflejar el comportamiento real del sistema.

### User Story Dependencies

```
[Phase 1: Setup]
       │
       ▼
[Phase 2: Foundational]
       ├─────────────────────────────┐
       ▼                             ▼
[Phase 3: US2 Ingesta]         [Phase 7: US5 Health]
       │
       ▼
[Phase 4: US1 RAG Q&A (MVP)]
       │
       ├─────────────────────────────┐
       ▼                             ▼
[Phase 5: US3 Herramientas]    [Phase 6: US4 Historial]
       │                             │
       └──────────────┬──────────────┘
                      ▼
       [Phase 8: Suite Evaluación (5 Casos)]
                      │
                      ▼
       [Phase 9: Terraform IaC]
                      │
                      ▼
       [Phase 10: Documentación Final]
```

---

## Parallel Opportunities

- **Fase 1 (Setup)**: T003 (`.env.example` y `.gitignore`) puede ejecutarse en paralelo con T001 y T002.
- **Fase 2 (Foundational)**: T005 (`logger.py`), T006 (`security.py`) y T009 (`sample_docs`) son completamente paralelizables al modificar archivos independientes.
- **Fase 3 (US2)**: T010 (tests de RAG) puede escribirse en paralelo con la definición del modelo.
- **Fase 5 (US3)**: T019 (tests de tools), T020 (Tool 1) y T021 (Tool 2) son paralelizables entre sí.
- **Fase 9 y 10 (IaC & Docs)**: T029 (`infra/terraform`), T031 (`architecture.md`), T032 (`technical_decisions.md`) y T033 (`ai_development_log.md`) pueden redactarse en paralelo.

---

## Implementation Strategy

### MVP First (Fases 1, 2, 3 y 4)
1. Completar Setup (Fase 1) y Foundational (Fase 2).
2. Implementar Ingesta documental (Fase 3: US2) e indexar documentos de muestra.
3. Implementar Consulta RAG (Fase 4: US1) con citas y abstención.
4. **Validación del MVP**: Verificar con `pytest tests/test_rag.py` que una consulta responde con citas de fuentes y se abstiene si no hay datos.

### Entrega Incremental
1. Añadir Agente y Herramientas controladas (Fase 5: US3) → Validar consulta de tickets y priorización.
2. Añadir Persistencia de Historial y Auditoría (Fase 6: US4) → Validar trazabilidad en `/history`.
3. Añadir Endpoint de Salud (Fase 7: US5) → Validar `/health`.
4. Ejecutar Suite de Evaluación de 5 casos obligatorios (Fase 8).
5. Validar Infraestructura Terraform (Fase 9).
6. Consolidar Documentación y Entregables (Fase 10).
