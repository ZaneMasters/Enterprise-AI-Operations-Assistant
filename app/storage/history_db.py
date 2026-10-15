"""Repositorio de persistencia en SQLite para historial de interacciones y auditoría."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import aiosqlite

from app.core.config import get_settings
from app.core.logger import logger


class HistoryRepository:
    """Gestiona el almacenamiento y consulta inmutable de las trazas de interacción."""

    def __init__(self, db_path: Optional[str] = None):
        default_path = get_settings().SQLITE_DB_PATH
        # En AWS Lambda el directorio raíz es de sólo lectura; el único directorio escribible es /tmp
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            default_path = "/tmp/history.db"

        self.db_path = db_path or default_path
        self._initialized = False
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def init_db(self) -> None:
        """Inicializa el esquema de la tabla de historial si no existe."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
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
                )
                """
            )
            # Índice para ordenamiento cronológico rápido
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_timestamp ON interaction_history (timestamp DESC)"
            )
            await db.commit()
            self._initialized = True
            logger.info("Esquema de base de datos SQLite de historial inicializado exitosamente.")

    async def _ensure_db(self) -> None:
        if not self._initialized:
            await self.init_db()

    async def save_interaction(
        self,
        interaction_id: str,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        tools_used: List[Dict[str, Any]],
        duration_ms: float,
        status: str,
        session_id: Optional[str] = None,
    ) -> None:
        """Registra una interacción de forma inmutable."""
        await self._ensure_db()
        timestamp = datetime.now(timezone.utc).isoformat()
        sources_json = json.dumps(sources, ensure_ascii=False)
        tools_used_json = json.dumps(tools_used, ensure_ascii=False)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO interaction_history (
                    interaction_id, session_id, timestamp, query, answer,
                    sources_json, tools_used_json, duration_ms, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    interaction_id,
                    session_id,
                    timestamp,
                    query,
                    answer,
                    sources_json,
                    tools_used_json,
                    duration_ms,
                    status,
                ),
            )
            await db.commit()

    async def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retorna las interacciones ordenadas cronológicamente de la más reciente a la más antigua.
        Limit acotado entre 1 y 100.
        """
        await self._ensure_db()
        clamped_limit = max(1, min(limit, 100))
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT interaction_id, session_id, timestamp, query, answer,
                       sources_json, tools_used_json, duration_ms, status
                FROM interaction_history
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (clamped_limit,),
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                results.append(
                    {
                        "interaction_id": row["interaction_id"],
                        "session_id": row["session_id"],
                        "timestamp": row["timestamp"],
                        "query": row["query"],
                        "answer": row["answer"],
                        "sources": json.loads(row["sources_json"]),
                        "tools_used": json.loads(row["tools_used_json"]),
                        "duration_ms": row["duration_ms"],
                        "status": row["status"],
                    }
                )
            return results


# Instancia por defecto
history_repo = HistoryRepository()
