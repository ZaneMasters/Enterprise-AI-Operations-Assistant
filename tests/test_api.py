"""Pruebas de integración de endpoints de la API REST."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_healthcheck_endpoint():
    """Valida que GET /health responda 200 OK con el estado del sistema."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "vectorstore_status" in data


@pytest.mark.asyncio
async def test_chat_rag_endpoint():
    """Valida el endpoint POST /chat para una consulta sobre procedimientos operativos."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"query": "¿Cuáles son los requisitos previos para actualizar la base de datos de producción?"}
        response = await ac.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "interaction_id" in data
        assert "answer" in data
        assert data["status"] == "SUCCESS"
        assert len(data["sources"]) > 0
        assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_chat_tool_execution_endpoint():
    """Valida que POST /chat invoque la herramienta de consulta de solicitudes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"query": "Por favor consultar el estado de la solicitud REQ-1001"}
        response = await ac.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert len(data["tools_used"]) > 0
        assert data["tools_used"][0]["tool_name"] == "consultar_estado_solicitud"


@pytest.mark.asyncio
async def test_history_endpoint():
    """Valida que GET /history devuelva las interacciones registradas."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/history?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "interactions" in data
        assert isinstance(data["interactions"], list)


@pytest.mark.asyncio
async def test_document_ingest_endpoint():
    """Valida la carga y procesamiento de un documento en POST /documents."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {
            "file": ("test_doc.md", b"# Documento de Prueba\nContenido operativo para validacion de API.", "text/markdown")
        }
        response = await ac.post("/documents", files=files)
        assert response.status_code == 201
        data = response.json()
        assert "doc_id" in data
        assert data["chunks_created"] > 0
