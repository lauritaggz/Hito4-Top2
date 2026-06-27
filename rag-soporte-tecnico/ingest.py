"""Ingesta documental: lee archivos locales, genera chunks y los indexa en ChromaDB."""

import sys
from pathlib import Path

import chromadb
import requests
from pypdf import PdfReader

import config
from ollama_utils import verify_ollama_or_exit


def get_embedding(text: str) -> list[float]:
    """Genera un embedding usando Ollama."""
    response = requests.post(
        f"{config.OLLAMA_BASE_URL}/api/embeddings",
        json={"model": config.OLLAMA_EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["embedding"]


def chunk_text(text: str) -> list[str]:
    """Divide texto en chunks con tamaño y solapamiento configurados."""
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + config.CHUNK_SIZE
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - config.CHUNK_OVERLAP
    return chunks


def read_pdf(path: Path) -> list[tuple[str, int]]:
    """Lee un PDF y devuelve tuplas (texto_página, número_página)."""
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append((page_text, i))
    return pages


def read_document(path: Path) -> list[tuple[str, dict]]:
    """
    Lee un documento y devuelve lista de (texto, metadatos_base).
    Para PDF devuelve un fragmento por página antes del chunking.
    """
    suffix = path.suffix.lower()

    if suffix in {".md", ".txt"}:
        text = path.read_text(encoding="utf-8")
        return [(text, {"source": path.name})]

    if suffix == ".pdf":
        return [
            (page_text, {"source": path.name, "page": page_num})
            for page_text, page_num in read_pdf(path)
        ]

    return []


def collect_documents(docs_path: Path) -> list[Path]:
    """Recopila archivos soportados desde el directorio de documentos."""
    if not docs_path.exists():
        print(f"Error: no existe el directorio {docs_path}")
        sys.exit(1)

    files = sorted(
        f for f in docs_path.iterdir()
        if f.is_file() and f.suffix.lower() in config.SUPPORTED_EXTENSIONS
    )
    return files


def main() -> None:
    verify_ollama_or_exit()

    docs_path = Path(config.DOCS_PATH)
    chroma_path = Path(config.CHROMA_PATH)

    files = collect_documents(docs_path)
    print(f"Archivos encontrados: {len(files)}")

    if not files:
        print("Error: no hay documentos para indexar en data/docs/")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(chroma_path))

    existing = [c.name for c in client.list_collections()]
    if config.COLLECTION_NAME in existing:
        client.delete_collection(config.COLLECTION_NAME)
        print(f"Colección '{config.COLLECTION_NAME}' eliminada.")

    collection = client.create_collection(name=config.COLLECTION_NAME)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    embeddings: list[list[float]] = []
    chunk_counter = 0

    for file_path in files:
        segments = read_document(file_path)
        file_chunk_index = 0

        for segment_text, base_metadata in segments:
            for chunk in chunk_text(segment_text):
                metadata = {
                    "source": base_metadata["source"],
                    "chunk": file_chunk_index,
                }
                if "page" in base_metadata:
                    metadata["page"] = base_metadata["page"]

                chunk_id = f"{file_path.stem}_{chunk_counter}"
                embedding = get_embedding(chunk)

                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append(metadata)
                embeddings.append(embedding)

                file_chunk_index += 1
                chunk_counter += 1

    print(f"Chunks generados: {len(documents)}")

    if documents:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    indexed = collection.count()
    print(f"Chunks indexados: {indexed}")
    print("Ingesta completada correctamente.")


if __name__ == "__main__":
    main()
