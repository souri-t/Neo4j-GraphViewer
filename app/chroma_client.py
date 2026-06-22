import os
from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings


class ChromaClient:
    def __init__(
        self,
        host: str | None = None,
        port: int | str | None = None,
        collection_name: str | None = None,
    ):
        self.host = host or os.getenv("CHROMA_HOST", "chromadb")
        self.port = int(port or os.getenv("CHROMA_PORT", "8000"))
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "document_chunks")
        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port,
            settings=Settings(anonymized_telemetry=False),
        )

    def verify(self) -> None:
        self.client.heartbeat()

    def get_collection(self):
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset_collection(self) -> None:
        names = [
            collection.name if hasattr(collection, "name") else collection
            for collection in self.client.list_collections()
        ]
        if self.collection_name in names:
            self.client.delete_collection(self.collection_name)
        self.get_collection()

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return
        collection = self.get_collection()
        collection.upsert(
            ids=[chunk["id"] for chunk in chunks],
            documents=[chunk["document"] for chunk in chunks],
            embeddings=[chunk["embedding"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
        )

    def describe_datasets(self) -> str:
        datasets = self.list_datasets()
        if not datasets:
            return "未登録"
        if len(datasets) == 1:
            return datasets[0]
        return f"複数: {', '.join(datasets)}"

    def list_datasets(self, batch_size: int = 1000) -> list[str]:
        collection = self.get_collection()
        total = collection.count()
        if total == 0:
            return []

        datasets: set[str] = set()
        for offset in range(0, total, batch_size):
            result = collection.get(
                limit=batch_size,
                offset=offset,
                include=["metadatas"],
            )
            for metadata in result.get("metadatas") or []:
                dataset = dataset_from_metadata(metadata or {})
                if dataset:
                    datasets.add(dataset)
        return sorted(datasets)

    def query(self, embedding: List[float], top_k: int = 10) -> list[Dict[str, Any]]:
        collection = self.get_collection()
        result = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances", "embeddings"],
        )
        ids = first_result(result.get("ids"))
        documents = first_result(result.get("documents"))
        metadatas = first_result(result.get("metadatas"))
        distances = first_result(result.get("distances"))
        embeddings = first_result(result.get("embeddings"))

        rows = []
        for index, chunk_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else None
            rows.append(
                {
                    "id": chunk_id,
                    "chunk_id": chunk_id,
                    "document": documents[index] if index < len(documents) else "",
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "distance": None if distance is None else float(distance),
                    "score": None if distance is None else 1.0 - float(distance),
                    "embedding": embeddings[index] if index < len(embeddings) else [],
                }
            )
        return rows


def dataset_from_metadata(metadata: dict[str, Any]) -> str:
    dataset = str(metadata.get("dataset") or "").strip()
    if dataset:
        return dataset

    path = str(metadata.get("path") or "").strip()
    if "/" not in path:
        return ""
    return path.split("/", 1)[0]


def first_result(value):
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not value:
        return []
    return value[0]
