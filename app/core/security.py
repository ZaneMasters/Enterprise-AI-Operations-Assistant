"""Módulo de seguridad: validación de entradas, sanitización y mitigación de prompt injection."""

import re
from typing import Tuple

MAX_QUERY_LENGTH = 2000
MIN_QUERY_LENGTH = 2

# Patrones heurísticos de intento de inyección directa de prompts
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)reveal\s+(your\s+)?(system\s+prompt|instructions|secret)",
    r"(?i)olvida\s+(todas\s+las\s+)?instrucciones\s+(previas|anteriores)",
    r"(?i)ignora\s+(las\s+)?instrucciones\s+(previas|anteriores)",
    r"(?i)muestra\s+(el\s+)?prompt\s+del\s+sistema",
    r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
    r"(?i)act\s+as\s+an\s+unrestricted\s+ai",
    r"(?i)bypass\s+(all\s+)?safety\s+filters",
    r"(?i)system\s*:\s*override",
]


def validate_and_sanitize_query(query: str) -> Tuple[bool, str, str]:
    """
    Valida la longitud y caracteres de la consulta.
    Retorna (is_valid, sanitized_query, error_message).
    """
    if not query or len(query.strip()) < MIN_QUERY_LENGTH:
        return False, "", "La consulta no puede estar vacía o tener menos de 2 caracteres."

    if len(query) > MAX_QUERY_LENGTH:
        return False, "", f"La consulta supera la longitud máxima permitida de {MAX_QUERY_LENGTH} caracteres."

    # Normalizar espacios y eliminar caracteres de control no imprimibles
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", query).strip()

    return True, sanitized, ""


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Evalúa si el texto contiene patrones evidentes de manipulación o inyección de prompts.
    Retorna (is_detected, pattern_matched).
    """
    for pattern in PROMPT_INJECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return True, match.group(0)
    return False, ""


def isolate_context_for_rag(chunks: list[str]) -> str:
    """
    Envuelve los fragmentos documentales recuperados dentro de etiquetas delimitadoras XML
    para prevenir inyecciones de prompt indirectas contenidas en los documentos.
    """
    isolated_parts = []
    for idx, chunk in enumerate(chunks, 1):
        clean_chunk = chunk.replace("</context_documents>", "").replace("<context_documents>", "")
        isolated_parts.append(f"<document_chunk id='{idx}'>\n{clean_chunk}\n</document_chunk>")

    return "<context_documents>\n" + "\n".join(isolated_parts) + "\n</context_documents>"
