"""Pipeline de ingesta documental: validación, extracción de texto, chunking e indexación vectorial."""

import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pypdf import PdfReader

from app.core.config import get_settings
from app.core.logger import logger


class DocumentIngestionService:
    """Servicio responsable del preprocesamiento e indexación vectorial de documentos."""

    def __init__(self, persist_directory: Optional[str] = None):
        self.settings = get_settings()
        self.persist_directory = persist_directory or self.settings.VECTOR_DB_PATH
        self.collection = None
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="operational_docs",
                metadata={"description": "Documentos técnicos y operativos para soporte RAG"}
            )
        except Exception as e:
            logger.info(f"ChromaDB no disponible en entorno de ingesta: {e}")

    def extract_text_from_file(self, file_path: str) -> str:
        """Extrae el contenido textual según la extensión del archivo (.md, .txt, .pdf)."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".md", ".txt"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()

        elif ext == ".pdf":
            reader = PdfReader(file_path)
            extracted = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                if text.strip():
                    extracted.append(f"[Página {page_num}]\n{text}")
            return "\n\n".join(extracted)

        else:
            raise ValueError(f"Formato de archivo no admitido: {ext}. Solo se admiten .md, .txt y .pdf.")

    def split_text_into_chunks(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        """
        Divide el texto recursivamente en fragmentos respetando párrafos y saltos de línea.
        """
        size = chunk_size or self.settings.CHUNK_SIZE
        overlap = chunk_overlap or self.settings.CHUNK_OVERLAP

        if not text.strip():
            return []

        # División inicial por dobles saltos de línea (párrafos)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # Si un solo párrafo supera el tamaño, subdividirlo por líneas
                if len(para) > size:
                    sub_lines = para.split("\n")
                    temp = ""
                    for line in sub_lines:
                        if len(temp) + len(line) + 1 <= size:
                            temp = f"{temp}\n{line}".strip()
                        else:
                            if temp:
                                chunks.append(temp)
                            temp = line
                    if temp:
                        chunks.append(temp)
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Aplicar solapamiento si hay más de un chunk
        if overlap > 0 and len(chunks) > 1:
            overlapped_chunks = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_tail = chunks[i - 1][-overlap:] if len(chunks[i - 1]) >= overlap else chunks[i - 1]
                overlapped_chunks.append(f"...{prev_tail}...\n{chunks[i]}")
            return overlapped_chunks

        return chunks

    def compute_file_hash(self, content_bytes: bytes) -> str:
        """Calcula el hash SHA-256 del contenido."""
        return hashlib.sha256(content_bytes).hexdigest()

    def ingest_document(
        self,
        filename: str,
        content: str,
        category: str = "general"
    ) -> Tuple[str, int]:
        """
        Procesa el texto de un documento, lo fragmenta y lo almacena en ChromaDB con metadatos.
        Retorna (doc_id, total_chunks).
        """
        if not content.strip():
            raise ValueError("El documento no contiene texto válido para indexar.")

        doc_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        chunks = self.split_text_into_chunks(content)

        if not chunks:
            raise ValueError("No se pudieron generar fragmentos válidos del documento.")

        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "filename": filename,
                "source": filename,
                "category": category,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "created_at": created_at
            }
            for i in range(len(chunks))
        ]

        # Inserción en ChromaDB si está disponible localmente
        if self.collection:
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Documento '{filename}' ({doc_id}) indexado exitosamente en ChromaDB con {len(chunks)} fragmentos.")
        else:
            logger.info(f"Modo Cloud/Serverless: Documento '{filename}' ({doc_id}) procesado exitosamente ({len(chunks)} fragmentos).")
        return doc_id, len(chunks)


# Instancia singleton
ingest_service = DocumentIngestionService()
