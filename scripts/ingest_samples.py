"""Script utilitario para ingesta masiva de documentos de prueba en ChromaDB."""

import os
import sys

# Agregar la raíz del repositorio al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.ingest import ingest_service
from app.core.logger import logger


def main():
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_docs"))
    if not os.path.exists(docs_dir):
        logger.error(f"Directorio de documentos de muestra no encontrado: {docs_dir}")
        return

    files = [f for f in os.listdir(docs_dir) if f.endswith((".md", ".txt", ".pdf"))]
    logger.info(f"Iniciando ingesta de {len(files)} documentos de prueba...")

    total_chunks = 0
    for file_name in files:
        full_path = os.path.join(docs_dir, file_name)
        try:
            content = ingest_service.extract_text_from_file(full_path)
            doc_id, count = ingest_service.ingest_document(
                filename=file_name,
                content=content,
                category="sample_procedure"
            )
            total_chunks += count
            print(f"[OK] Ingerido '{file_name}' ({doc_id}) -> {count} fragmentos.")
        except Exception as e:
            print(f"[ERROR] Error al procesar '{file_name}': {e}")

    print(f"\nIngesta completada exitosamente. Total de fragmentos indexados: {total_chunks}")


if __name__ == "__main__":
    main()
