import os
from typing import Iterable, List

import requests


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_URL", "http://ollama:11434")).rstrip("/")
        self.model = model or os.getenv("EMBEDDING_MODEL", "embeddinggemma")

    def embed(self, text: str) -> List[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: Iterable[str]) -> List[List[float]]:
        inputs = [text.strip() for text in texts]
        if not inputs:
            return []

        try:
            return self._embed_batch(inputs)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return [self._embed_legacy(text) for text in inputs]
            raise

    def _embed_batch(self, inputs: list[str]) -> List[List[float]]:
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": inputs},
            timeout=180,
        )
        self._raise_with_hint(response)
        data = response.json()
        embeddings = data.get("embeddings")
        if not embeddings:
            raise RuntimeError(f"Ollama embedding response did not include embeddings: {data}")
        return embeddings

    def _embed_legacy(self, text: str) -> List[float]:
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=180,
        )
        self._raise_with_hint(response)
        data = response.json()
        embedding = data.get("embedding")
        if not embedding:
            raise RuntimeError(f"Ollama embedding response did not include embedding: {data}")
        return embedding

    def _raise_with_hint(self, response: requests.Response) -> None:
        if response.ok:
            return
        hint = ""
        try:
            message = response.json().get("error", "")
        except ValueError:
            message = response.text
        if "not found" in message.lower() or response.status_code == 404:
            hint = f" Model '{self.model}' may not be pulled yet. Run: docker exec -it rag-ollama ollama pull {self.model}"
        raise requests.HTTPError(f"Ollama request failed: {response.status_code} {message}.{hint}", response=response)
