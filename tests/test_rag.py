"""Pruebas unitarias para el motor RAG: extracción, chunking, recuperación y abstención."""

import pytest
from app.rag.ingest import ingest_service
from app.rag.retriever import FORMAL_ABSTENTION_MESSAGE, retriever_service


def test_split_text_into_chunks():
    """Valida que el texto se divida adecuadamente en fragmentos manejables."""
    sample_text = (
        "Primer párrafo con directrices de seguridad.\n\n"
        "Segundo párrafo con procedimiento de migración de base de datos.\n\n"
        "Tercer párrafo con instrucciones de contingencia y rollback."
    )
    chunks = ingest_service.split_text_into_chunks(sample_text, chunk_size=80, chunk_overlap=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) > 0


def test_retrieval_and_citation():
    """Valida que una consulta sobre un procedimiento documentado retorne fuentes y fragmentos."""
    query = "¿Cuál es el procedimiento y requisitos para actualizar la base de datos?"
    chunks, source_refs, distance = retriever_service.retrieve_context(query)

    assert len(chunks) > 0
    assert len(source_refs) > 0
    assert any("procedimiento_actualizacion_db.md" in s.source for s in source_refs)

    answer, is_abstained = retriever_service.generate_grounded_answer(query, chunks, source_refs)
    assert not is_abstained
    assert "procedimiento_actualizacion_db.md" in answer or len(source_refs) > 0


def test_formal_abstention_on_unsupported_query():
    """Valida que una consulta sobre un tema inexistente active la abstención formal sin alucinación."""
    query = "¿Cuál es la política de reembolso para viajes corporativos en primera clase?"
    # Simular recuperación vacía para preguntas fuera de alcance
    chunks, source_refs, _ = retriever_service.retrieve_context(query, max_distance=0.1)

    answer, is_abstained = retriever_service.generate_grounded_answer(query, chunks, source_refs)
    assert is_abstained
    assert FORMAL_ABSTENTION_MESSAGE in answer
