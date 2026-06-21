import traceback

import streamlit as st

from chroma_client import ChromaClient
from ollama_client import OllamaClient


@st.cache_resource
def get_chroma_client() -> ChromaClient:
    return ChromaClient()


@st.cache_resource
def get_ollama_client() -> OllamaClient:
    return OllamaClient()


def show_error(message: str, exc: Exception | None = None) -> None:
    st.error(message)
    if exc is not None:
        with st.expander("詳細エラー"):
            st.code("".join(traceback.format_exception_only(type(exc), exc)).strip())


def search_chunks(query: str, top_k: int) -> list[dict]:
    embedding = get_ollama_client().embed(query)
    return get_chroma_client().query(embedding, top_k=top_k)


def format_number(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"
