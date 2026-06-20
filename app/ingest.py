import hashlib
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np

from neo4j_client import Neo4jClient
from ollama_client import OllamaClient


SUPPORTED_EXTENSIONS = {".txt", ".md"}
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 140


@dataclass
class IngestStats:
    documents: int
    chunks: int
    chunk_similarity_edges: int
    document_similarity_edges: int


def ingest_docs(
    docs_dir: str | Path | None = None,
    reset: bool = True,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    similar_top_k: int = 4,
    similarity_threshold: float = 0.74,
) -> IngestStats:
    docs_path = Path(docs_dir or os.getenv("DOCS_DIR", "/app/docs"))
    files = list_document_files(docs_path)
    if not files:
        raise FileNotFoundError(f"No supported documents found under {docs_path}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    ollama = OllamaClient()
    neo4j = Neo4jClient()
    neo4j.verify()

    if reset:
        neo4j.clear_graph()

    all_chunks: list[dict] = []
    documents: list[dict] = []

    for path in files:
        text = read_text(path)
        if not text.strip():
            continue
        relative_path = str(path.relative_to(docs_path))
        document_id = stable_id(relative_path)
        title = derive_title(path, text)
        document = {"id": document_id, "title": title, "path": relative_path, "text": text}
        raw_chunks = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
        embeddings = ollama.embed_many(raw_chunks)
        if len(embeddings) != len(raw_chunks):
            raise RuntimeError(
                f"Ollama returned {len(embeddings)} embeddings for {len(raw_chunks)} chunks in {relative_path}"
            )

        if embeddings and not all_chunks:
            neo4j.init_schema(len(embeddings[0]))

        chunks = []
        for index, (chunk, embedding) in enumerate(zip(raw_chunks, embeddings)):
            chunk_id = stable_id(f"{relative_path}:{index}:{chunk[:80]}")
            chunk_record = {
                "id": chunk_id,
                "document_id": document_id,
                "document_title": title,
                "text": chunk,
                "chunk_index": index,
                "embedding": embedding,
                "entities": extract_entities(chunk),
            }
            chunks.append(chunk_record)
            all_chunks.append(chunk_record)

        neo4j.upsert_document(document, chunks)
        documents.append(document)

    chunk_pairs = build_chunk_similarity_pairs(all_chunks, top_k=similar_top_k, threshold=similarity_threshold)
    neo4j.create_chunk_similarities(chunk_pairs)

    document_pairs = build_document_similarity_pairs(all_chunks, threshold=similarity_threshold)
    neo4j.create_document_similarities(document_pairs)

    return IngestStats(
        documents=len(documents),
        chunks=len(all_chunks),
        chunk_similarity_edges=len(chunk_pairs),
        document_similarity_edges=len(document_pairs),
    )


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


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", normalized) if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(split_long_text(paragraph, chunk_size, overlap))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current.strip())
            current = paragraph

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


def extract_entities(text: str) -> list[dict[str, str]]:
    candidates: set[str] = set()
    candidates.update(re.findall(r"(?m)^#{1,6}\s+(.+)$", text))
    candidates.update(re.findall(r"[A-Z][A-Za-z0-9']+(?:\s+[A-Z][A-Za-z0-9']+){1,4}", text))
    candidates.update(re.findall(r"[「『](.{2,30}?)[」』]", text))
    candidates.update(re.findall(r"\b[一-龥ァ-ン]{3,12}\b", text))

    entities = []
    for candidate in candidates:
        name = re.sub(r"\s+", " ", candidate).strip(" -:：、。,.()[]")
        if not name or len(name) > 60:
            continue
        if len(name) < 2:
            continue
        entity_type = "Topic"
        if re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", name):
            entity_type = "NamedEntity"
        elif re.search(r"[一-龥]", name):
            entity_type = "JapaneseTerm"
        entities.append({"name": name, "type": entity_type})
    return sorted(entities, key=lambda item: item["name"])[:12]


def build_chunk_similarity_pairs(chunks: list[dict], top_k: int, threshold: float) -> list[dict]:
    if len(chunks) < 2:
        return []
    matrix = normalize_embeddings([chunk["embedding"] for chunk in chunks])
    scores = matrix @ matrix.T
    pairs: list[dict] = []

    for i, source in enumerate(chunks):
        order = np.argsort(scores[i])[::-1]
        selected = 0
        for j in order:
            if i == j:
                continue
            if source["document_id"] == chunks[j]["document_id"]:
                continue
            score = float(scores[i, j])
            if score < threshold:
                continue
            source_id, target_id = sorted([source["id"], chunks[j]["id"]])
            pair_key = (source_id, target_id)
            if any(existing["source_id"] == pair_key[0] and existing["target_id"] == pair_key[1] for existing in pairs):
                continue
            pairs.append({"source_id": source_id, "target_id": target_id, "score": score})
            selected += 1
            if selected >= top_k:
                break
    return pairs


def build_document_similarity_pairs(chunks: list[dict], threshold: float) -> list[dict]:
    by_doc: Dict[str, list[np.ndarray]] = {}
    for chunk in chunks:
        by_doc.setdefault(chunk["document_id"], []).append(np.array(chunk["embedding"], dtype=np.float32))
    doc_vectors = {
        doc_id: np.mean(np.stack(vectors), axis=0)
        for doc_id, vectors in by_doc.items()
        if vectors
    }
    rows = list(doc_vectors.items())
    pairs: list[dict] = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            left_id, left_vector = rows[i]
            right_id, right_vector = rows[j]
            score = cosine(left_vector, right_vector)
            if score >= threshold:
                pairs.append({"source_id": left_id, "target_id": right_id, "score": score})
    return pairs


def normalize_embeddings(embeddings: Iterable[Iterable[float]]) -> np.ndarray:
    matrix = np.array(list(embeddings), dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if math.isclose(denominator, 0.0):
        return 0.0
    return float(np.dot(left, right) / denominator)


def stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


if __name__ == "__main__":
    stats = ingest_docs()
    print(stats)
