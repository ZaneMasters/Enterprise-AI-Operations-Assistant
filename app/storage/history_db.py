import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import aiosqlite
import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.core.logger import logger


class HistoryRepository:
    """Gestiona el almacenamiento y consulta inmutable de las trazas de interacción en SQLite y DynamoDB."""

    def __init__(self, db_path: Optional[str] = None):
        settings = get_settings()
        default_path = settings.SQLITE_DB_PATH
        # En AWS Lambda el directorio raíz es de sólo lectura; el único directorio escribible es /tmp
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            default_path = "/tmp/history.db"

        self.db_path = db_path or default_path
        self._initialized = False
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.dynamodb_table_name = settings.DYNAMODB_TABLE_NAME or os.environ.get("DYNAMODB_TABLE_NAME")
        self.aws_region = settings.BEDROCK_REGION or os.environ.get("AWS_REGION", "us-east-1")
        self._dynamodb_table = None

    def _get_dynamo_table(self):
        """Inicializa de manera lazy la tabla de DynamoDB."""
        if self._dynamodb_table is None and self.dynamodb_table_name:
            try:
                dynamodb = boto3.resource("dynamodb", region_name=self.aws_region)
                self._dynamodb_table = dynamodb.Table(self.dynamodb_table_name)
            except Exception as e:
                logger.warning(f"No se pudo inicializar cliente DynamoDB: {e}")
        return self._dynamodb_table

    async def init_db(self) -> None:
        """Inicializa el esquema de la tabla de historial si no existe en SQLite."""
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
        """Registra una interacción de forma inmutable en SQLite y DynamoDB (si está configurado)."""
        await self._ensure_db()
        timestamp = datetime.now(timezone.utc).isoformat()
        sources_json = json.dumps(sources, ensure_ascii=False)
        tools_used_json = json.dumps(tools_used, ensure_ascii=False)

        # 1. Guardar en SQLite local
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

        # 2. Guardar en Amazon DynamoDB si está configurado en el entorno
        table = self._get_dynamo_table()
        if table:
            try:
                # DynamoDB requiere Decimal para números no enteros
                # Convertimos estructuras anidadas asegurando compatibilidad con DynamoDB
                clean_sources = json.loads(sources_json)
                clean_tools = json.loads(tools_used_json)

                item = {
                    "interaction_id": interaction_id,
                    "timestamp": timestamp,
                    "session_id": session_id or "default",
                    "query": query,
                    "answer": answer,
                    "sources": clean_sources,
                    "tools_used": clean_tools,
                    "duration_ms": Decimal(str(round(duration_ms, 2))),
                    "status": status,
                }
                table.put_item(Item=item)
                logger.info(f"Interacción {interaction_id} registrada con éxito en DynamoDB ({self.dynamodb_table_name}).")
            except Exception as e:
                logger.error(f"Error al persistir interacción en DynamoDB: {e}")

    async def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retorna las interacciones ordenadas cronológicamente de la más reciente a la más antigua.
        Limit acotado entre 1 y 100. Consulta DynamoDB si está disponible; de lo contrario SQLite.
        """
        clamped_limit = max(1, min(limit, 100))
        table = self._get_dynamo_table()

        if table:
            try:
                response = table.scan(Limit=clamped_limit)
                items = response.get("Items", [])
                # Ordenar por timestamp descendente
                items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                results = []
                for item in items[:clamped_limit]:
                    results.append(
                        {
                            "interaction_id": item.get("interaction_id"),
                            "session_id": item.get("session_id"),
                            "timestamp": item.get("timestamp"),
                            "query": item.get("query"),
                            "answer": item.get("answer"),
                            "sources": item.get("sources", []),
                            "tools_used": item.get("tools_used", []),
                            "duration_ms": float(item.get("duration_ms", 0.0)),
                            "status": item.get("status"),
                        }
                    )
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Error consultando DynamoDB, recurriendo a SQLite: {e}")

        # Fallback a SQLite
        await self._ensure_db()
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
