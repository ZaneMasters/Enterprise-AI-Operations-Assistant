# Quickstart Guide: Enterprise AI Operations Assistant

**Feature**: `001-ai-operations-assistant`  
**Prerequisites**: Python 3.11+, Terraform v1.16+ (opcional para IaC)

---

## 1. Configuración del Entorno Virtual

```powershell
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

---

## 2. Variables de Entorno

Copiar el archivo de ejemplo y configurar las credenciales:

```powershell
copy .env.example .env
```

Contenido mínimo de `.env`:
```ini
ENVIRONMENT=development
PORT=8000
VECTOR_DB_PATH=./data/vectorstore
SQLITE_DB_PATH=./data/history.db
REQUESTS_DB_PATH=./data/requests_db.json
# Proveedor LLM (OpenAI o AWS Bedrock o Mock)
LLM_PROVIDER=openai
OPENAI_API_KEY=tu-api-key-aqui
```

---

## 3. Inicializar Datos de Prueba e Ingesta

El proyecto incluye documentos operativos sintéticos en `data/sample_docs/` y la base de solicitudes en `data/requests_db.json`.

```powershell
# Ingesta inicial de los documentos de prueba en ChromaDB
python scripts/ingest_samples.py
```

---

## 4. Iniciar el Servidor Backend (FastAPI)

```powershell
uvicorn app.main:app --reload --port 8000
```

- Documentación interactiva Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Healthcheck: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 5. Ejecutar Pruebas Automatizadas y Suite de Evaluación

```powershell
# Ejecutar todas las pruebas unitarias e integración
pytest -v

# Ejecutar específicamente la suite de evaluación de calidad (5 casos obligatorios)
pytest tests/test_evaluation.py -v
```

---

## 6. Validación de Infraestructura (Terraform)

Para validar la sintaxis y plan de los recursos de AWS sin costo:

```powershell
cd infra/terraform
terraform init
terraform validate
terraform plan
```
