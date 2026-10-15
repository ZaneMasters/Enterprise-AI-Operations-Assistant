"""Herramientas controladas del agente: consulta de solicitudes y clasificación de prioridad."""

import json
import os
import re
from typing import Any, Dict
from pydantic import BaseModel, Field

from app.api.schemas import PriorityAssessment, PriorityLevel
from app.core.config import get_settings
from app.core.logger import logger


# --- Esquemas de Entrada para Herramientas ---

class ConsultarEstadoInput(BaseModel):
    solicitud_id: str = Field(
        ...,
        description="Identificador único de la solicitud (formato REQ-XXXX, ej. REQ-1001)",
        pattern=r"^REQ-\d+$"
    )


class ClasificarSolicitudInput(BaseModel):
    categoria: str = Field(..., description="Categoría de la incidencia (ej. INFRAESTRUCTURA, SEGURIDAD, ACCESO, BUG)")
    impacto: str = Field(..., description="Nivel de impacto: ALTO, MEDIO, BAJO")
    urgencia: str = Field(..., description="Nivel de urgencia: ALTA, MEDIA, BAJA")
    descripcion: str = Field(..., min_length=5, max_length=1000, description="Descripción técnica de la situación")


# --- Implementación de Herramientas ---

def consultar_estado_solicitud(solicitud_id: str) -> Dict[str, Any]:
    """
    Herramienta 1: Consulta el estado de una solicitud en la base de datos sintética.
    Retorna los datos de la solicitud o indica que no fue encontrada.
    """
    # Validación sintáctica
    normalized_id = solicitud_id.strip().upper()
    if not re.match(r"^REQ-\d+$", normalized_id):
        return {
            "encontrada": False,
            "mensaje": f"Formato de identificador inválido: '{solicitud_id}'. Debe ser REQ-XXXX (ej. REQ-1001)."
        }

    db_path = get_settings().REQUESTS_DB_PATH
    if not os.path.exists(db_path):
        logger.error(f"Base de solicitudes no encontrada en ruta: {db_path}")
        return {"encontrada": False, "mensaje": "Base de datos de solicitudes no disponible temporalmente."}

    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            requests = data.get("requests", [])

        for req in requests:
            if req.get("request_id") == normalized_id:
                logger.info(f"Solicitud {normalized_id} encontrada exitosamente.")
                return {
                    "encontrada": True,
                    "solicitud": req,
                    "mensaje": f"Solicitud {normalized_id} encontrada con estado {req.get('status')}."
                }

        logger.info(f"Solicitud {normalized_id} no encontrada en base de datos.")
        return {
            "encontrada": False,
            "mensaje": f"La solicitud '{normalized_id}' no existe en los registros del sistema."
        }
    except Exception as e:
        logger.error(f"Error al leer base de datos de solicitudes: {e}")
        return {"encontrada": False, "mensaje": "Error interno al consultar la solicitud."}


def clasificar_y_recomendar_solicitud(
    categoria: str,
    impacto: str,
    urgencia: str,
    descripcion: str
) -> Dict[str, Any]:
    """
    Herramienta 2: Evalúa los parámetros y clasifica la prioridad en tres niveles deterministas:
    - ALTA: Caída de servicio, interrupción crítica de operaciones o riesgo de seguridad.
    - MEDIA: Degradación funcional o afectación parcial sin paro total.
    - BAJA: Consultas informativas, tareas programadas o soporte ordinario no crítico.
    """
    cat_upper = categoria.strip().upper()
    imp_upper = impacto.strip().upper()
    urg_upper = urgencia.strip().upper()
    desc_lower = descripcion.lower()

    # Criterios para prioridad ALTA
    palabras_criticas = ["caida", "corte", "indisponible", "vulnerabilidad", "fuga", "compromiso", "bloqueo", "outage"]
    es_riesgo_seguridad = cat_upper == "SEGURIDAD" or any(p in desc_lower for p in ["seguridad", "vulnerabilidad", "fuga"])
    es_caida_servicio = imp_upper == "ALTO" and urg_upper == "ALTA"
    tiene_palabra_critica = any(p in desc_lower for p in palabras_criticas)

    if es_caida_servicio or es_riesgo_seguridad or tiene_palabra_critica:
        priority = PriorityLevel.ALTA
        effort = 1
        rule = "Regla de Incidencia Crítica / Seguridad (Afectación total o riesgo de seguridad inminente)"
        justification = (
            f"Se clasifica como ALTA debido a {rule.lower()}. "
            f"La categoría es {cat_upper} con impacto {imp_upper} y urgencia {urg_upper}."
        )
    elif imp_upper in ["MEDIO", "ALTO"] or urg_upper in ["MEDIA", "ALTA"] or "degradacion" in desc_lower or "lentitud" in desc_lower:
        priority = PriorityLevel.MEDIA
        effort = 3
        rule = "Regla de Degradación Parcial (Afectación funcional sin paro total del servicio)"
        justification = (
            f"Se clasifica como MEDIA debido a {rule.lower()}. "
            f"Presenta impacto {imp_upper} y urgencia {urg_upper} con afectación contenida."
        )
    else:
        priority = PriorityLevel.BAJA
        effort = 5
        rule = "Regla de Soporte General (Consulta ordinaria, mantenimiento programado o tarea no bloqueante)"
        justification = (
            f"Se clasifica como BAJA debido a {rule.lower()}. "
            f"La solicitud corresponde a tareas rutinarias sin impacto operativo directo."
        )

    assessment = PriorityAssessment(
        priority=priority,
        estimated_effort_days=effort,
        rule_applied=rule,
        justification=justification
    )

    logger.info(f"Clasificación completada: {assessment.priority.value} - {rule}")
    return assessment.model_dump()


# Metadata de herramientas para tool calling
AVAILABLE_TOOLS = [
    {
        "name": "consultar_estado_solicitud",
        "description": "Consulta el estado actual y detalles de una solicitud operativa mediante su identificador REQ-XXXX.",
        "parameters": ConsultarEstadoInput.model_json_schema(),
        "function": consultar_estado_solicitud
    },
    {
        "name": "clasificar_y_recomendar_solicitud",
        "description": "Clasifica la prioridad de una solicitud o incidencia en ALTA, MEDIA o BAJA según reglas de severidad.",
        "parameters": ClasificarSolicitudInput.model_json_schema(),
        "function": clasificar_y_recomendar_solicitud
    }
]
