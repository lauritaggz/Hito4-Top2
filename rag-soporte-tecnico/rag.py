"""Recuperación y generación RAG usando ChromaDB y Ollama."""

import re
from dataclasses import dataclass

import chromadb
import requests

import config
from ollama_utils import OllamaError, verify_ollama


@dataclass
class RAGResult:
    answer: str
    sources: list[str]
    fragments: list[dict]


class RAGError(Exception):
    """Error general del pipeline RAG."""


class EmptyIndexError(RAGError):
    """La base vectorial no tiene documentos indexados."""


def check_ollama() -> None:
    verify_ollama()


def get_embedding(text: str) -> list[float]:
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": config.OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except requests.RequestException as exc:
        raise OllamaError(f"Error al generar embedding: {exc}") from exc


def get_collection():
    from pathlib import Path

    chroma_path = Path(config.CHROMA_PATH)
    if not chroma_path.exists():
        raise EmptyIndexError(
            "No hay base vectorial. Ejecuta primero: python ingest.py"
        )

    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        collection = client.get_collection(config.COLLECTION_NAME)
    except ValueError as exc:
        raise EmptyIndexError(
            "No hay colección indexada. Ejecuta primero: python ingest.py"
        ) from exc

    if collection.count() == 0:
        raise EmptyIndexError(
            "La base vectorial está vacía. Ejecuta primero: python ingest.py"
        )

    return collection


def is_index_ready() -> tuple[bool, str]:
    """Comprueba si la base vectorial está lista para consultas."""
    try:
        get_collection()
        return True, ""
    except EmptyIndexError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Error al acceder a ChromaDB: {exc}"


def retrieve_context(question: str) -> list[dict]:
    collection = get_collection()
    query_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=config.TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    fragments = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, distance in zip(docs, metas, distances):
        fragments.append(
            {
                "text": doc,
                "source": meta.get("source", "desconocido"),
                "chunk": meta.get("chunk"),
                "page": meta.get("page"),
                "distance": distance,
            }
        )

    return fragments


def build_prompt(question: str, fragments: list[dict]) -> str:
    context_parts = []
    for i, frag in enumerate(fragments, start=1):
        source = frag["source"]
        page_info = f", página {frag['page']}" if frag.get("page") else ""
        context_parts.append(
            f"[Fragmento {i} — {source}{page_info}]\n{frag['text']}"
        )

    context = "\n\n".join(context_parts)

    return (
        f"Contexto:\n{context}\n\n"
        f"Pregunta del usuario: {question}\n\n"
        "Responde solo en español, directo al grano, sin meta-comentarios."
    )


_META_TAIL_PATTERNS = (
    r"\s+Then Fuentes usadas.*$",
    r"\s+Fuentes usadas:.*$",
    r"\s+Second sentence:.*$",
    r"\s+In Fragmento \d+.*$",
    r"\s+Then .*$",
    r"\s+Wait, the user.*$",
    r"\s+Yes, the answer is.*$",
    r"\s+Let me check.*$",
)

_ENGLISH_CUT_MARKERS = (
    r"^Okay,\s+",
    r"^Wait,\s+",
    r"^Let me\s+",
    r"^First,\s+",
    r"\s+Wait,\s+",
    r"\s+Let me\s+",
    r"\s+Okay,\s+",
    r"\s+First,\s+",
    r"\s+Yes,\s+the answer",
    r"\s+The user'?s question",
    r"\s+Fragmento\s+\d+\s+is",
    r"\s+I should\s+",
    r"\s+I need to\s+",
    r"\s+So the answer",
    r"\s+So\s+",
    r"\s+So$",
    r"\s+Now,\s+",
    r"\s+Looking at\s+",
)


def _truncate_english_reasoning(text: str) -> str:
    """Corta el texto en el primer marcador de razonamiento en inglés."""
    earliest = len(text)
    for pattern in _ENGLISH_CUT_MARKERS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match and match.start() < earliest:
            earliest = match.start()
    return text[:earliest].strip()


def _strip_meta_tail(text: str) -> str:
    """Elimina razonamiento o meta-texto al final de la respuesta."""
    result = text.strip().strip("\"'")
    for pattern in _META_TAIL_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.DOTALL | re.IGNORECASE)
    return result.strip()


def _finalize_answer(text: str) -> str:
    """Limpia meta-texto y razonamiento en inglés de la respuesta final."""
    if not text:
        return ""
    return _truncate_english_reasoning(_strip_meta_tail(text)).strip()


def _is_meta_line(line: str) -> bool:
    """Detecta líneas de meta-comentario del modelo, no respuesta útil."""
    lower = line.lower().strip()
    meta_markers = (
        "the answer would be",
        "the answer is",
        "second sentence",
        "in fragmento",
        "then fuentes",
        "fuentes usadas:",
        "fragmento 1",
        "fragmento 2",
        "it's written as",
        "it is written as",
    )
    return any(marker in lower for marker in meta_markers)


def _is_english_reasoning(line: str) -> bool:
    """Detecta líneas de razonamiento interno en inglés de modelos qwen3."""
    lower = line.lower().strip()
    if not lower:
        return True

    prefixes = (
        "okay",
        "okay, let's",
        "first",
        "let me",
        "let's see",
        "wait",
        "i should",
        "i need",
        "the user",
        "yes,",
        "i'm",
        "now,",
        "next,",
        "also,",
        "check if",
        "make sure",
        "looking at",
        "based on",
    )
    if lower.startswith(prefixes):
        return True

    if not re.search(r"[áéíóúñ¿¡]", line, flags=re.IGNORECASE):
        english_words = (" the ", " should ", " need ", " user ", " answer ", " context ")
        if any(word in lower for word in english_words):
            return True

    return False


def _normalize_text(text: str) -> str:
    return re.sub(r"[^\w\sáéíóúñ]", "", text.lower(), flags=re.IGNORECASE).strip()


def _echoes_question(answer: str, question: str) -> bool:
    """Detecta si la respuesta solo repite o parafrasea mínimamente la pregunta."""
    q = _normalize_text(question)
    a = _normalize_text(answer)
    if not q or not a:
        return False
    if a == q:
        return True
    return a.startswith(q) and len(a) < len(q) + 30


def _is_valid_spanish_answer(text: str, question: str = "") -> bool:
    """Comprueba que la respuesta sea texto útil en español, no razonamiento en inglés."""
    if not text or len(text.strip()) < 50:
        return False
    if _is_english_reasoning(text) or _is_meta_line(text):
        return False
    if question and _echoes_question(text, question):
        return False

    lower = text.lower()
    if any(
        phrase in lower
        for phrase in (
            "the user is asking",
            "let's see",
            "let me check",
            "how to create",
            "is asking how",
        )
    ):
        return False

    if re.search(r"\s+(so|wait|let|yes|the|i)\s*$", text, flags=re.IGNORECASE):
        return False

    has_spanish_chars = bool(re.search(r"[áéíóúñ¿¡]", text, flags=re.IGNORECASE))
    spanish_words = (
        " es ", " son ", " para ", " ejecuta ", " comando ", " debe ",
        " construir ", " crea ", " crear ", " indica ", " asigna ",
        " una ", " un ", " el ", " la ", " los ", " las ", " con ", " del ", " al ",
        " cómo ", " imagen ", " docker ", " git ", " linux ",
    )
    has_spanish_words = any(word in lower for word in spanish_words)
    return has_spanish_chars or has_spanish_words


def _clean_fragment_text(text: str) -> str:
    """Convierte un fragmento markdown en texto legible para la respuesta."""
    parts: list[str] = []
    in_code = False

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            parts.append(f"Comando: `{line}`")
            continue
        if line.startswith("#"):
            continue
        if line.startswith("- "):
            parts.append(line[2:])
        else:
            parts.append(line)

    return " ".join(parts)


def fallback_from_fragments(fragments: list[dict]) -> str:
    """Respuesta extractiva desde los fragmentos cuando el LLM no responde bien."""
    for frag in fragments:
        cleaned = _clean_fragment_text(frag["text"])
        if len(cleaned) < 40:
            continue

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
        if not sentences:
            continue

        excerpt = " ".join(sentences[:3])
        if len(excerpt) > 500:
            excerpt = excerpt[:500].rsplit(" ", 1)[0] + "."
        return excerpt

    return config.NO_INFO_RESPONSE


def clean_thinking_tags(text: str) -> str:
    """Elimina bloques de razonamiento interno de modelos qwen3."""
    think_open = "<" + "think" + ">"
    think_close = "</" + "think" + ">"
    patterns = [
        re.escape(think_open) + r".*?" + re.escape(think_close),
        r"<think>.*?</think>",
    ]
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def extract_final_answer(text: str) -> str:
    """
    qwen3 puede mezclar razonamiento en inglés con la respuesta final.
    Extrae solo el texto útil en español para mostrar al usuario.
    """
    cleaned = clean_thinking_tags(text)
    if not cleaned:
        return ""

    for pattern in (
        r"(?:The answer would be|The answer is|Respuesta):\s*(.+)",
        r"(?:In Spanish|En español):\s*[\"']?(.+)",
        r"(?:Final answer|Respuesta final):\s*(.+)",
    ):
        match = re.search(pattern, cleaned, flags=re.DOTALL | re.IGNORECASE)
        if match:
            answer = _finalize_answer(match.group(1))
            if _is_valid_spanish_answer(answer):
                return answer

    truncated = _truncate_english_reasoning(cleaned)
    spanish_parts = []
    for line in truncated.splitlines():
        line = line.strip()
        if not line or _is_english_reasoning(line) or _is_meta_line(line):
            continue
        part = _finalize_answer(line)
        if _is_valid_spanish_answer(part):
            spanish_parts.append(part)

    if spanish_parts:
        return "\n\n".join(spanish_parts)

    final = _finalize_answer(truncated)
    if _is_valid_spanish_answer(final):
        return final
    return ""


def generate_answer(prompt: str) -> str:
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": config.OLLAMA_LLM_MODEL,
                "messages": [
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "think": False,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": config.OLLAMA_NUM_PREDICT,
                },
            },
            timeout=config.OLLAMA_GENERATE_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        raw = data.get("message", {}).get("content", "") or data.get("response", "")
        answer = extract_final_answer(raw)
        if _is_valid_spanish_answer(answer):
            return answer
        return ""
    except requests.RequestException as exc:
        raise OllamaError(
            f"Error al generar respuesta con Ollama: {exc}\n"
            "La primera consulta con qwen3:4b puede tardar 1-3 minutos en hardware "
            "limitado. Reintenta o verifica con: ollama ps"
        ) from exc


def extract_sources(fragments: list[dict]) -> list[str]:
    seen = set()
    sources = []
    for frag in fragments:
        name = frag["source"]
        if name not in seen:
            seen.add(name)
            sources.append(name)
    return sources


def query(question: str) -> RAGResult:
    """Ejecuta el pipeline RAG completo."""
    if not question.strip():
        raise RAGError("La pregunta no puede estar vacía.")

    check_ollama()
    fragments = retrieve_context(question)

    if not fragments:
        return RAGResult(
            answer=config.NO_INFO_RESPONSE,
            sources=[],
            fragments=[],
        )

    prompt = build_prompt(question, fragments)
    answer = generate_answer(prompt)

    if not _is_valid_spanish_answer(answer, question):
        answer = fallback_from_fragments(fragments)

    # Normalizar respuesta cuando el modelo no encontró información
    no_info_variants = [
        "no encontré información suficiente",
        "no encontre informacion suficiente",
        "no contiene la respuesta",
    ]
    if any(v in answer.lower() for v in no_info_variants):
        answer = config.NO_INFO_RESPONSE

    sources = extract_sources(fragments)

    return RAGResult(
        answer=answer,
        sources=sources,
        fragments=fragments,
    )
