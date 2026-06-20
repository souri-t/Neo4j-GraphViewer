import os
import traceback

import streamlit as st
import streamlit.components.v1 as components

from graph_view import build_graph_html
from ingest import ingest_docs
from neo4j_client import Neo4jClient
from ollama_client import OllamaClient


st.set_page_config(page_title="Neo4j + Ollama 文書検索デモ", layout="wide")


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


st.title("Neo4j + Ollama 文書検索・グラフビューデモ")

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

search_col, detail_col = st.columns([1, 1], gap="large")

with search_col:
    st.subheader("意味検索")
    query = st.text_input("検索文", placeholder="例: デス・スターへの攻撃、憲法改正の議論")
    limit = st.slider("検索件数", min_value=3, max_value=20, value=8)

    if query:
        try:
            st.session_state["results"] = run_search(query, limit)
        except Exception as exc:
            show_error("検索に失敗しました。先に文書取り込みを実行しているか確認してください。", exc)
            st.session_state["results"] = []

    results = st.session_state.get("results", [])
    if results:
        labels = [
            f"{index + 1}. {row['title']} / Chunk {row['chunk_index']} / score={row['score']:.3f}"
            for index, row in enumerate(results)
        ]
        selected_index = st.selectbox("検索結果", range(len(results)), format_func=lambda index: labels[index])
        selected = results[selected_index]

        for index, row in enumerate(results, start=1):
            with st.container(border=True):
                st.markdown(f"**{index}. {row['title']}**")
                st.caption(f"`{row['path']}` / Chunk {row['chunk_index']} / 類似度 {row['score']:.4f}")
                st.write(row["text"])

        st.session_state["selected_chunk_id"] = selected["chunk_id"]
    elif query:
        st.info("検索結果がありません。文書取り込み後に別の検索文を試してください。")
    else:
        st.info("検索文を入力すると、Neo4j のベクトルインデックスから近い Chunk を取得します。")

with detail_col:
    st.subheader("詳細・グラフビュー")
    selected_chunk_id = st.session_state.get("selected_chunk_id")
    if not selected_chunk_id:
        st.info("検索結果を選択すると、中心 Chunk の周辺グラフを表示します。")
    else:
        selected_result = next((row for row in st.session_state.get("results", []) if row["chunk_id"] == selected_chunk_id), None)
        if selected_result:
            st.markdown(f"**{selected_result['title']}**")
            st.caption(f"`{selected_result['path']}` / Chunk {selected_result['chunk_index']} / score={selected_result['score']:.4f}")
            with st.expander("選択 Chunk 本文", expanded=True):
                st.write(selected_result["text"])

        try:
            graph_data = get_neo4j_client().graph_context(selected_chunk_id)
            if graph_data["nodes"]:
                components.html(build_graph_html(graph_data), height=650, scrolling=True)
            else:
                st.info("グラフデータが見つかりませんでした。")
        except Exception as exc:
            show_error("グラフビューの取得に失敗しました。", exc)
