import os
import traceback

import streamlit as st

from ingest import ingest_docs
from neo4j_client import Neo4jClient
from ollama_client import OllamaClient


@st.cache_resource
def get_neo4j_client() -> Neo4jClient:
    return Neo4jClient()


@st.cache_resource
def get_ollama_client() -> OllamaClient:
    return OllamaClient()


def run_search(query: str, limit: int):
    embedding = get_ollama_client().embed(query)
    return get_neo4j_client().search_chunks(embedding, limit=limit)


def show_error(message: str, exc: Exception | None = None) -> None:
    st.error(message)
    if exc is not None:
        with st.expander("詳細エラー"):
            st.code("".join(traceback.format_exception_only(type(exc), exc)).strip())


def result_labels(results: list[dict]) -> list[str]:
    return [
        f"{index + 1}. {row['title']} / Chunk {row['chunk_index']} / score={row['score']:.3f}"
        for index, row in enumerate(results)
    ]


def render_sidebar() -> None:
    with st.sidebar:
        st.header("接続設定")
        st.caption(f"Neo4j: `{os.getenv('NEO4J_URI', 'bolt://neo4j:7687')}`")
        st.caption(f"Ollama: `{os.getenv('OLLAMA_URL', 'http://ollama:11434')}`")
        st.caption(f"Embedding: `{os.getenv('EMBEDDING_MODEL', 'embeddinggemma')}`")
        st.caption(f"Docs: `{os.getenv('DOCS_DIR', '/app/docs')}`")

        if st.button("文書を取り込む", type="primary", use_container_width=True):
            with st.spinner("docs 配下の文書を読み込み、Embedding とグラフを作成しています..."):
                try:
                    stats = ingest_docs()
                    st.session_state["ingested"] = True
                    st.success(
                        f"取り込み完了: {stats.documents} 文書 / {stats.chunks} チャンク / "
                        f"{stats.chunk_similarity_edges} Chunk類似 / {stats.document_similarity_edges} Document類似"
                    )
                except Exception as exc:
                    show_error("文書取り込みに失敗しました。Neo4j と Ollama の起動、embeddinggemma の pull 状態を確認してください。", exc)

        if st.button("接続確認", use_container_width=True):
            try:
                get_neo4j_client().verify()
                get_ollama_client().embed("connection test")
                st.success("Neo4j と Ollama に接続できました。")
            except Exception as exc:
                show_error("接続確認に失敗しました。", exc)


def search_controls(state_prefix: str, default_limit: int = 8) -> tuple[str, int, list[dict]]:
    query = st.text_input(
        "検索文",
        placeholder="例: デス・スターへの攻撃、憲法改正の議論",
        key=f"{state_prefix}_query",
    )
    limit = st.slider("検索件数", min_value=3, max_value=20, value=default_limit, key=f"{state_prefix}_limit")

    results_key = f"{state_prefix}_results"
    if query:
        try:
            st.session_state[results_key] = run_search(query, limit)
        except Exception as exc:
            show_error("検索に失敗しました。先に文書取り込みを実行しているか確認してください。", exc)
            st.session_state[results_key] = []

    return query, limit, st.session_state.get(results_key, [])


def select_result(results: list[dict], state_prefix: str) -> dict | None:
    if not results:
        return None
    selected_index = st.selectbox(
        "検索結果",
        range(len(results)),
        format_func=lambda index: result_labels(results)[index],
        key=f"{state_prefix}_selected_index",
    )
    selected = results[selected_index]
    st.session_state[f"{state_prefix}_selected_chunk_id"] = selected["chunk_id"]
    st.session_state["selected_chunk_id"] = selected["chunk_id"]
    return selected
