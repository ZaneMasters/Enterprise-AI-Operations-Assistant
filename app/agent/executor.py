"""Ejecutor del agente: enrutamiento de intenciones, Tool Calling, RAG y trazabilidad."""

import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from app.api.schemas import (
    InteractionStatus,
    QueryResponse,
    SourceReference,
    ToolExecutionResult,
)
from app.agent.tools import (
    AVAILABLE_TOOLS,
    clasificar_y_recomendar_solicitud,
    consultar_estado_solicitud,
)
from app.core.logger import correlation_id_ctx, logger
from app.core.security import (
    detect_prompt_injection,
    validate_and_sanitize_query,
)
from app.rag.retriever import retriever_service
from app.storage.history_db import history_repo


class AgentExecutor:
    """Orquesta la ejecución del agente, selección de herramientas, RAG y auditoría."""

    def __init__(self):
        self.retriever = retriever_service
        self.history = history_repo

    async def execute(self, query: str, session_id: Optional[str] = None) -> QueryResponse:
        """Punto de entrada principal para procesar una consulta de usuario."""
        start_time = time.perf_counter()
        interaction_id = str(uuid.uuid4())
        correlation_id_ctx.set(interaction_id)

        logger.info(f"Iniciando procesamiento de consulta ({interaction_id}): '{query[:50]}...'")

        # 1. Validación y Sanitización de Entrada (FR-011)
        is_valid, sanitized_query, error_msg = validate_and_sanitize_query(query)
        if not is_valid:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            await self._persist(interaction_id, query, error_msg, [], [], duration_ms, InteractionStatus.ERROR, session_id)
            return QueryResponse(
                interaction_id=interaction_id,
                query=query,
                answer=error_msg,
                sources=[],
                tools_used=[],
                duration_ms=duration_ms,
                status=InteractionStatus.ERROR,
            )

        # 2. Mitigación de Prompt Injection Directa (RNF-01, SC-005)
        is_injection, matched_pattern = detect_prompt_injection(sanitized_query)
        if is_injection:
            logger.warning(f"Intento de prompt injection detectado en consulta: '{matched_pattern}'")
            rejection_msg = (
                "La consulta contiene patrones o instrucciones no autorizadas que violan las políticas de seguridad. "
                "La operación ha sido denegada de acuerdo con las directrices de gobernanza."
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            await self._persist(interaction_id, query, rejection_msg, [], [], duration_ms, InteractionStatus.ERROR, session_id)
            return QueryResponse(
                interaction_id=interaction_id,
                query=query,
                answer=rejection_msg,
                sources=[],
                tools_used=[],
                duration_ms=duration_ms,
                status=InteractionStatus.ERROR,
            )

        # 3. Detección y Enrutamiento de Herramientas Operativas (FR-006, FR-007)
        tools_executed: List[ToolExecutionResult] = []
        tool_handled, tool_answer = self._try_dispatch_tools(sanitized_query, tools_executed)

        if tool_handled:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            await self._persist(interaction_id, sanitized_query, tool_answer, [], tools_executed, duration_ms, InteractionStatus.SUCCESS, session_id)
            return QueryResponse(
                interaction_id=interaction_id,
                query=sanitized_query,
                answer=tool_answer,
                sources=[],
                tools_used=tools_executed,
                duration_ms=duration_ms,
                status=InteractionStatus.SUCCESS,
            )

        # 4. Pipeline RAG Documental (FR-001, FR-002, FR-003)
        chunks, source_refs, best_distance = self.retriever.retrieve_context(sanitized_query)
        answer, is_abstained = self.retriever.generate_grounded_answer(sanitized_query, chunks, source_refs)
        status = InteractionStatus.ABSTAINED if is_abstained else InteractionStatus.SUCCESS

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        saved_sources = [] if is_abstained else [s.model_dump() for s in source_refs]
        await self._persist(interaction_id, sanitized_query, answer, saved_sources, [], duration_ms, status, session_id)

        return QueryResponse(
            interaction_id=interaction_id,
            query=sanitized_query,
            answer=answer,
            sources=source_refs if not is_abstained else [],
            tools_used=[],
            duration_ms=duration_ms,
            status=status,
        )

    def _try_dispatch_tools(
        self,
        query: str,
        tools_executed: List[ToolExecutionResult]
    ) -> Tuple[bool, str]:
        """Evalúa si la consulta requiere la invocación de herramientas operativas."""
        q_upper = query.upper()
        q_lower = query.lower()

        # Detección de Tool 1: Consulta de estado de solicitud (REQ-XXXX)
        req_match = re.search(r"REQ-\d+", q_upper)
        if req_match or any(k in q_lower for k in ["solicitud", "ticket", "estado de la peticion"]):
            req_id = req_match.group(0) if req_match else "REQ-1001"
            logger.info(f"Despachando Herramienta 1: consultar_estado_solicitud para ID: {req_id}")
            result = consultar_estado_solicitud(req_id)
            tools_executed.append(
                ToolExecutionResult(
                    tool_name="consultar_estado_solicitud",
                    parameters={"solicitud_id": req_id},
                    output=result
                )
            )
            if result.get("encontrada"):
                s = result["solicitud"]
                answer = (
                    f"Información de la Solicitud {s.get('request_id')}:\n"
                    f"- Título: {s.get('title')}\n"
                    f"- Estado: {s.get('status')}\n"
                    f"- Categoría: {s.get('category')}\n"
                    f"- Solicitante: {s.get('requester')}\n"
                    f"- Detalles: {s.get('details')}"
                )
            else:
                answer = result.get("mensaje", f"La solicitud {req_id} no fue encontrada en los registros.")
            return True, answer

        # Detección de Tool 2: Clasificación de prioridad de solicitud
        if any(k in q_lower for k in ["clasificar", "priorizar", "prioridad", "evaluar severidad", "calcular esfuerzo"]):
            logger.info("Despachando Herramienta 2: clasificar_y_recomendar_solicitud")
            # Extraer heurísticas de la consulta
            categoria = "SEGURIDAD" if "seguridad" in q_lower else ("INFRAESTRUCTURA" if "infraestructura" in q_lower or "servidor" in q_lower else "OPERACIONES")
            impacto = "ALTO" if any(w in q_lower for w in ["caida", "alto", "critico", "bloqueo", "urgente"]) else ("MEDIO" if "degradacion" in q_lower or "medio" in q_lower else "BAJO")
            urgencia = "ALTA" if any(w in q_lower for w in ["inmediata", "alta", "urgente", "ya"]) else ("MEDIA" if "media" in q_lower else "BAJA")

            result = clasificar_y_recomendar_solicitud(
                categoria=categoria,
                impacto=impacto,
                urgencia=urgencia,
                descripcion=query
            )
            tools_executed.append(
                ToolExecutionResult(
                    tool_name="clasificar_y_recomendar_solicitud",
                    parameters={"categoria": categoria, "impacto": impacto, "urgencia": urgencia, "descripcion": query},
                    output=result
                )
            )
            answer = (
                f"Evaluación de Prioridad Completada:\n"
                f"- Nivel Asignado: {result.get('priority')}\n"
                f"- Esfuerzo Estimado: {result.get('estimated_effort_days')} días hábiles\n"
                f"- Regla Aplicada: {result.get('rule_applied')}\n"
                f"- Justificación: {result.get('justification')}"
            )
            return True, answer

        return False, ""

    async def _persist(
        self,
        interaction_id: str,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        tools_used: List[Any],
        duration_ms: float,
        status: InteractionStatus,
        session_id: Optional[str] = None
    ) -> None:
        """Persiste la traza en la base de datos de historial."""
        try:
            tools_dict = [t.model_dump() if hasattr(t, "model_dump") else t for t in tools_used]
            await self.history.save_interaction(
                interaction_id=interaction_id,
                query=query,
                answer=answer,
                sources=sources,
                tools_used=tools_dict,
                duration_ms=duration_ms,
                status=status.value,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Error al guardar historial de interacción: {e}")


# Instancia singleton
agent_executor = AgentExecutor()
