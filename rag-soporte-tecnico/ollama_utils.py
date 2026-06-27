"""Utilidades compartidas para verificar Ollama y modelos requeridos."""

import sys

import requests

import config


class OllamaError(Exception):
    """Ollama no está disponible o falta algún modelo requerido."""


def _installed_models() -> list[str]:
    response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
    response.raise_for_status()
    return [model["name"] for model in response.json().get("models", [])]


def _model_available(required: str, installed: list[str]) -> bool:
    required_base = required.split(":")[0]
    for name in installed:
        if name == required or name.startswith(f"{required}:"):
            return True
        if name.split(":")[0] == required_base:
            return True
    return False


def verify_ollama() -> None:
    """
    Verifica que Ollama responda y que existan los modelos configurados.
    Lanza OllamaError con mensaje claro si algo falla.
    """
    try:
        installed = _installed_models()
    except requests.RequestException as exc:
        linux_hint = ""
        if "host.docker.internal" in config.OLLAMA_BASE_URL:
            linux_hint = (
                "\n\nEn Linux nativo (sin Docker Desktop), el contenedor puede no "
                "alcanzar Ollama por host.docker.internal.\n"
                "Prueba con:\n"
                "  docker compose -f docker-compose.yml -f docker-compose.linux.yml "
                "--profile ingest run --rm rag-ingest\n"
                "  docker compose -f docker-compose.yml -f docker-compose.linux.yml up rag-app\n"
                "O configura Ollama en el host con: OLLAMA_HOST=0.0.0.0:11434"
            )
        raise OllamaError(
            f"Ollama no está disponible en {config.OLLAMA_BASE_URL}.\n"
            "Asegúrate de que Ollama esté corriendo en el computador anfitrión.\n"
            "En Docker Desktop (Windows/macOS), el contenedor se conecta al host "
            "mediante host.docker.internal."
            f"{linux_hint}\n"
            f"Detalle: {exc}"
        ) from exc

    missing = []
    for model in (config.OLLAMA_LLM_MODEL, config.OLLAMA_EMBED_MODEL):
        if not _model_available(model, installed):
            missing.append(model)

    if missing:
        lines = [
            "Faltan modelos en Ollama:",
            *[f"  - {model}" for model in missing],
            "",
            "Instálalos en el host con:",
        ]
        if config.OLLAMA_EMBED_MODEL in missing:
            lines.append(f"  ollama pull {config.OLLAMA_EMBED_MODEL}")
        if config.OLLAMA_LLM_MODEL in missing:
            lines.append(
                f"  ollama pull {config.OLLAMA_LLM_MODEL}  "
                "(o verifica con: ollama list)"
            )
        raise OllamaError("\n".join(lines))


def verify_ollama_or_exit() -> None:
    """Verifica Ollama e imprime el error en consola si falla."""
    try:
        verify_ollama()
    except OllamaError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
