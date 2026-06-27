import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Variables del sistema tienen prioridad; dotenv no las sobrescribe.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.docker")


def _resolve_path(value: str) -> str:
    """Convierte rutas relativas en rutas absolutas respecto al proyecto."""
    path = Path(value)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    return str(path)


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "qwen3:4b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_PATH = _resolve_path(os.getenv("CHROMA_PATH", "./chroma_db"))
DOCS_PATH = _resolve_path(os.getenv("DOCS_PATH", "./data/docs"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "soporte_tecnico")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K = int(os.getenv("TOP_K", "4"))
OLLAMA_GENERATE_TIMEOUT = int(os.getenv("OLLAMA_GENERATE_TIMEOUT", "600"))
# qwen3 consume tokens en razonamiento interno; 300 deja respuestas cortadas.
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "512"))
# Distancia L2 máxima del mejor fragmento para considerarlo relevante (ChromaDB).
MAX_DISTANCE_THRESHOLD = float(os.getenv("MAX_DISTANCE_THRESHOLD", "280"))

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}

SYSTEM_PROMPT = (
    "Eres un asistente de soporte técnico. Responde SOLO en español, de forma directa, "
    "usando únicamente el contexto entregado. No inventes información externa. "
    "No escribas en inglés. No expliques tu razonamiento. No menciones fragmentos, "
    "fuentes ni cómo construiste la respuesta. "
    "Si el contexto no contiene la respuesta, responde exactamente: "
    "'No encontré información suficiente en los documentos disponibles para responder con seguridad.' "
    "Máximo 4 frases claras y completas."
)

NO_INFO_RESPONSE = (
    "No encontré información suficiente en los documentos disponibles "
    "para responder con seguridad."
)
