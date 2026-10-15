# Implementation Plan: Enterprise AI Operations Assistant

**Branch**: `001-ai-operations-assistant` | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ai-operations-assistant/spec.md`

---

## Summary

Construir un Agente RAG empresarial y API REST con FastAPI en Python para la gestión de solicitudes y consultas operativas internas. Incorpora un pipeline RAG con ChromaDB, dos herramientas de agente controladas (`consultar_estado_solicitud` y `clasificar_y_recomendar_solicitud`), auditoría y persistencia en SQLite, mecanismos de seguridad contra prompt injection directa e indirecta, una suite de evaluación automatizada con 5 casos de prueba obligatorios, e infraestructura como código declarativa en Terraform para AWS.

---

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Pydantic v2, Uvicorn, ChromaDB, LangChain Core (o cliente nativo LLM), PyPDF / Python-docx, pytest, aiosqlite  
**Storage**: ChromaDB (almacenamiento vectorial en `./data/vectorstore`), SQLite (`./data/history.db` para historial/auditoría), JSON mock (`./data/requests_db.json` para solicitudes operativas)  
**Testing**: pytest (suite de integración y `tests/test_evaluation.py` con 5 casos de calidad)  
**Target Platform**: Ejecución local multiplataforma (Windows/Linux/macOS) y despliegue serverless en AWS (HTTP API Gateway + AWS Lambda + Bedrock + S3 + DynamoDB)  
**Live Endpoint**: `https://rvcbgebxx7.execute-api.us-east-1.amazonaws.com`  
**Project Type**: Web Service (API REST con FastAPI + Mangum) + CLI scripts + IaC (Terraform)  
**Performance Goals**: P95 < 5 segundos en consultas estándar RAG  
**Constraints**: Secretos aislados en `.env`, 0 fugas de stack traces en errores, abstención obligatoria ante falta de datos fundamentados, mitigación de prompt injection  
**Scale/Scope**: Módulo backend atómico y autónomo, sin frontend innecesario (Principio I de la constitución)

---

## Constitution Check

*GATE: Evaluation against `.specify/memory/constitution.md`*

- [x] **Principio I (Alcance estricto)**: No se añade frontend independiente ni sobreingeniería; solo API, RAG, agente, historial y tests.
- [x] **Principio II (Arquitectura simple)**: Código desacoplado en carpetas con responsabilidad única (`app/api`, `app/rag`, `app/agent`, `app/core`).
- [x] **Principio III (RAG fundamentado)**: Filtros de similitud, citas de fuentes explícitas y abstención formal sin alucinación.
- [x] **Principio IV (Agente controlado)**: 2 herramientas implementadas con esquemas Pydantic estrictos e idempotentes.
- [x] **Principio V (Seguridad por diseño)**: Manejo de `.env`, validación de inputs, delimitación de contexto para mitigar prompt injection indirecto.
- [x] **Principio VI (IaC con Terraform)**: Módulos reproducibles en `infra/terraform/` parametrizados con `hashicorp/aws`.
- [x] **Principio VII (Pruebas basadas en evidencia)**: 5 casos de evaluación verificables con `pytest`.
- [x] **Principio VIII (Observabilidad)**: Logs estructurados con `request_id` y auditoría en endpoint `/history`.
- [x] **Principio IX (AI-CDL)**: Documentación explícita del uso asistido de IA en `docs/ai_development_log.md`.
- [x] **Principio X (Documentación fidedigna)**: README completo, diagrama de arquitectura y justificación de decisiones técnicas.

---

## Project Structure

### Documentation & Spec Kit Artifacts

```text
specs/001-ai-operations-assistant/
├── spec.md              # Especificación funcional y criterios de éxito
├── plan.md              # Este archivo (Plan técnico de implementación)
├── research.md          # Decisiones tecnológicas y análisis de alternativas
├── data-model.md        # Entidades del dominio y esquemas Pydantic
├── quickstart.md        # Guía paso a paso de ejecución y validación
├── contracts/
│   └── openapi.yaml     # Contrato OpenAPI 3.0 de los endpoints REST
└── checklists/
    └── requirements.md  # Checklist de calidad superado
```

### Source Code Layout

```text
enterprise-rag-agent/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # Endpoints: /health, /query, /documents, /history
│   │   └── schemas.py         # Modelos Pydantic Request/Response
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Pydantic Settings (.env)
│   │   ├── logger.py          # Structured logging con request_id
│   │   └── security.py        # Validaciones de entrada y sanitización
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingest.py          # Extracción, chunking y carga en ChromaDB
│   │   └── retriever.py       # Búsqueda semántica, umbral de similitud y citas
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── tools.py           # Herramienta 1 (tickets) y Herramienta 2 (priorización)
│   │   └── executor.py        # Agente con Tool Calling y system prompt delimitado
│   ├── storage/
│   │   ├── __init__.py
│   │   └── history_db.py      # Repositorio SQLite para trazabilidad y auditoría
│   └── main.py                # Fábrica de aplicación FastAPI y middlewares
├── data/
│   ├── sample_docs/           # Documentos técnicos operativos sintéticos
│   │   ├── procedimiento_actualizacion_db.md
│   │   └── politica_seguridad_accesos.md
│   └── requests_db.json       # Mock DB de solicitudes para la Herramienta 1
├── infra/
│   └── terraform/             # IaC para AWS
│       ├── main.tf            # ECS Fargate, S3, DynamoDB, IAM
│       ├── variables.tf       # Variables configurables (región, tags)
│       └── outputs.tf         # Outputs de infraestructura
├── tests/
│   ├── __init__.py
│   ├── test_api.py            # Tests de integración de endpoints FastAPI
│   ├── test_rag.py            # Tests unitarios de ingest y recuperación
│   ├── test_tools.py          # Tests unitarios de las 2 herramientas del agente
│   └── test_evaluation.py     # 5 casos de evaluación de calidad requeridos
├── docs/
│   ├── architecture.md        # Diagrama de arquitectura y flujo de componentes
│   ├── technical_decisions.md # Registro de decisiones y trade-offs
│   └── ai_development_log.md  # Bitácora AI-CDL (punto 5.4 de la prueba)
├── scripts/
│   └── ingest_samples.py      # Script utilitario para indexación rápida
├── .env.example
├── requirements.txt
└── README.md
```

---

## Complexity Tracking

| Decisión | Por qué es necesaria | Alternativa más simple descartada |
| :--- | :--- | :--- |
| **ChromaDB local persistente** | Permite vector search con metadatos y citas exactas sin depender de servicios cloud externos durante la evaluación. | Almacenar vectores en memoria simple (se pierde el estado entre reinicios del servidor). |
| **SQLite para historial** | Garantiza persistencia estructurada y consulta eficiente de auditoría para el endpoint `/history`. | Archivo de log de texto plano (difícil de filtrar y consultar por API de forma tipada). |
| **Terraform declarativo en AWS** | Demuestra criterio de producción y madurez de nube requeridos para un perfil Semi-senior / Senior. | Explicación en texto sin código de infraestructura. |
