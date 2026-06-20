import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from chroma_client import ChromaClient
from ollama_client import OllamaClient


SUPPORTED_EXTENSIONS = {".txt", ".md"}
DEFAULT_CHUNK_SEPARATOR = "\n\n"
DEFAULT_CHUNK_SEPARATOR_DISPLAY = "\\n\\n"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
MAX_CHUNK_SIZE = 4000


@dataclass
class IngestStats:
    documents: int
    chunks: int


def ingest_docs(
    docs_dir: str | Path | None = None,
    reset: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    chunk_separator: str = DEFAULT_CHUNK_SEPARATOR,
    separator_is_regex: bool = False,
) -> IngestStats:
    docs_path = Path(docs_dir or os.getenv("DOCS_DIR", "/app/docs"))
    files = list_document_files(docs_path)
    if not files:
        raise FileNotFoundError(f"No .txt or .md documents found under {docs_path}")

    ollama = OllamaClient()
    chroma = ChromaClient()
    chroma.verify()

    if reset:
        chroma.reset_collection()

    documents = 0
    chunks_written = 0

    for path in files:
        text = read_text(path)
        if not text.strip():
            continue

        relative_path = str(path.relative_to(docs_path))
        document_id = stable_id(relative_path)
        title = derive_title(path, text)
        raw_chunks = chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
            separator=chunk_separator,
            separator_is_regex=separator_is_regex,
        )
        embeddings = ollama.embed_many(raw_chunks)
        if len(embeddings) != len(raw_chunks):
            raise RuntimeError(
                f"Ollama returned {len(embeddings)} embeddings for {len(raw_chunks)} chunks in {relative_path}"
            )

        chunks = []
        for index, (chunk, embedding) in enumerate(zip(raw_chunks, embeddings)):
            chunks.append(
                {
                    "id": stable_id(f"{relative_path}:{index}"),
                    "document": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "document_id": document_id,
                        "title": title,
                        "path": relative_path,
                        "chunk_index": index,
                        "source_type": path.suffix.lower().lstrip("."),
                        "chunk_separator": chunk_separator,
                        "chunk_separator_is_regex": separator_is_regex,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                    },
                }
            )

        chroma.upsert_chunks(chunks)
        documents += 1
        chunks_written += len(chunks)

    return IngestStats(documents=documents, chunks=chunks_written)


def list_document_files(docs_path: Path) -> list[Path]:
    return sorted(path for path in docs_path.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def derive_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        clean = line.strip().lstrip("#").strip()
        if clean:
            return clean[:120]
    return path.stem.replace("_", " ").replace("-", " ").title()


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    separator: str = DEFAULT_CHUNK_SEPARATOR,
    separator_is_regex: bool = False,
) -> list[str]:
    validate_chunk_settings(chunk_size, overlap, separator)
    normalized = text.strip()
    units = split_by_separator(normalized, separator=separator, separator_is_regex=separator_is_regex)
    chunks: list[str] = []
    current = ""

    for unit in units:
        if len(unit) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(split_long_text(unit, chunk_size, overlap))
            continue

        candidate = f"{current}{unit}" if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current.strip())
            current = apply_overlap(current, overlap) + unit
            if len(current) > chunk_size:
                chunks.extend(split_long_text(current, chunk_size, overlap))
                current = ""

    if current:
        chunks.append(current.strip())

    return [chunk for chunk in chunks if chunk]


def split_long_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def split_by_separator(text: str, separator: str, separator_is_regex: bool) -> list[str]:
    if separator_is_regex:
        try:
            pattern = re.compile(separator)
        except re.error as exc:
            raise ValueError(f"Invalid chunk separator regex: {exc}") from exc
        if pattern.match("") is not None:
            raise ValueError("Chunk separator regex must not match an empty string")
        return split_by_regex(text, pattern)

    actual_separator = decode_separator(separator)
    parts = text.split(actual_separator)
    units = []
    for index, part in enumerate(parts):
        if not part.strip():
            continue
        suffix = actual_separator if index < len(parts) - 1 else ""
        units.append(f"{part}{suffix}")
    return units


def split_by_regex(text: str, pattern: re.Pattern[str]) -> list[str]:
    units = []
    start = 0
    for match in pattern.finditer(text):
        end = match.end()
        unit = text[start:end]
        if unit.strip():
            units.append(unit)
        start = end
    tail = text[start:]
    if tail.strip():
        units.append(tail)
    return units


def validate_chunk_settings(chunk_size: int, overlap: int, separator: str) -> None:
    if chunk_size < 1 or chunk_size > MAX_CHUNK_SIZE:
        raise ValueError(f"Chunk size must be between 1 and {MAX_CHUNK_SIZE} characters")
    if overlap < 0:
        raise ValueError("Chunk overlap must be 0 or greater")
    if overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size")
    if not separator:
        raise ValueError("Chunk separator must not be empty")


def decode_separator(separator: str) -> str:
    decoded = (
        separator.replace("\\r\\n", "\r\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\r", "\r")
    )
    if not decoded:
        raise ValueError("Chunk separator must not be empty")
    return decoded


def apply_overlap(text: str, overlap: int) -> str:
    if overlap <= 0:
        return ""
    return text[-overlap:]


def stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


if __name__ == "__main__":
    stats = ingest_docs()
    print(stats)
