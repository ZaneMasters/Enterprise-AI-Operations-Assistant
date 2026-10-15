"""Pruebas unitarias para las herramientas operativas del agente."""

import pytest
from app.agent.tools import (
    clasificar_y_recomendar_solicitud,
    consultar_estado_solicitud,
)
from app.api.schemas import PriorityLevel


def test_consultar_estado_solicitud_existente():
    """Valida la consulta exitosa de una solicitud sintética existente (REQ-1001)."""
    result = consultar_estado_solicitud("REQ-1001")
    assert result["encontrada"] is True
    assert result["solicitud"]["request_id"] == "REQ-1001"
    assert result["solicitud"]["status"] == "APROBADO"


def test_consultar_estado_solicitud_inexistente():
    """Valida el manejo controlado ante una solicitud que no existe."""
    result = consultar_estado_solicitud("REQ-9999")
    assert result["encontrada"] is False
    assert "no existe" in result["mensaje"]


def test_consultar_estado_solicitud_formato_invalido():
    """Valida el rechazo ante un identificador malformado."""
    result = consultar_estado_solicitud("INVALID_FORMAT")
    assert result["encontrada"] is False
    assert "inválido" in result["mensaje"]


def test_clasificar_solicitud_alta():
    """Valida la clasificación determinista en prioridad ALTA para riesgos o caídas."""
    result = clasificar_y_recomendar_solicitud(
        categoria="SEGURIDAD",
        impacto="ALTO",
        urgencia="ALTA",
        descripcion="Vulnerabilidad crítica detectada en puerto SSH de producción con intento de fuga."
    )
    assert result["priority"] == PriorityLevel.ALTA.value
    assert result["estimated_effort_days"] == 1
    assert "Seguridad" in result["rule_applied"] or "Crítica" in result["rule_applied"]


def test_clasificar_solicitud_media():
    """Valida la clasificación en prioridad MEDIA para degradación parcial."""
    result = clasificar_y_recomendar_solicitud(
        categoria="INFRAESTRUCTURA",
        impacto="MEDIO",
        urgencia="MEDIA",
        descripcion="Degradación parcial y lentitud observada en respuestas de microservicio."
    )
    assert result["priority"] == PriorityLevel.MEDIA.value
    assert result["estimated_effort_days"] == 3


def test_clasificar_solicitud_baja():
    """Valida la clasificación en prioridad BAJA para consultas de soporte rutinarias."""
    result = clasificar_y_recomendar_solicitud(
        categoria="OPERACIONES",
        impacto="BAJO",
        urgencia="BAJA",
        descripcion="Consulta sobre horario programado para actualización de certificados."
    )
    assert result["priority"] == PriorityLevel.BAJA.value
    assert result["estimated_effort_days"] == 5
