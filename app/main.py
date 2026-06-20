import os
import traceback

import streamlit as st
import streamlit.components.v1 as components

from chroma_client import ChromaClient
from graph_view import build_graph_html, build_virtual_graph
from ingest import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SEPARATOR_DISPLAY, DEFAULT_CHUNK_SIZE, MAX_CHUNK_SIZE, ingest_docs
from ollama_client import OllamaClient


st.set_page_config(page_title="ChromaDB + Ollama 文書検索デモ", layout="wide")


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


def search(query: str, top_k: int) -> list[dict]:
    embedding = get_ollama_client().embed(query)
    return get_chroma_client().query(embedding, top_k=top_k)


def format_number(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


st.title("ChromaDB + Ollama 文書検索・仮想グラフビューデモ")

with st.sidebar:
    st.header("操作")
    top_k = st.slider("TopK", min_value=3, max_value=30, value=10)
    similarity_threshold = st.slider("グラフ表示用の類似度閾値", min_value=0.0, max_value=1.0, value=0.78, step=0.01)

    st.header("チャンク設定")
    chunk_separator = st.text_input("チャンク区切り文字", value=DEFAULT_CHUNK_SEPARATOR_DISPLAY)
    separator_is_regex = st.checkbox("正規表現として扱う", value=False)
    chunk_size = st.number_input(
        "最大チャンク長（文字数）",
        min_value=1,
        max_value=MAX_CHUNK_SIZE,
        value=DEFAULT_CHUNK_SIZE,
        step=50,
    )
    chunk_overlap = st.number_input(
        "チャンクのオーバーラップ（文字数）",
        min_value=0,
        max_value=max(int(chunk_size) - 1, 0),
        value=min(DEFAULT_CHUNK_OVERLAP, max(int(chunk_size) - 1, 0)),
        step=10,
    )
    overlap_ratio = float(chunk_overlap) / float(chunk_size) if chunk_size else 0.0
    if overlap_ratio < 0.10 or overlap_ratio > 0.25:
        st.warning("Difyではオーバーラップをチャンク長の10〜25%に設定することが推奨されています。")

    reset_before_ingest = st.checkbox("取り込み前にChromaDBをリセット（推奨）", value=True)

    if st.button("文書を取り込む", type="primary", use_container_width=True):
        with st.spinner("docs 配下の .txt / .md を読み込み、Embedding を ChromaDB に保存しています..."):
            try:
                stats = ingest_docs(
                    reset=reset_before_ingest,
                    chunk_size=int(chunk_size),
                    chunk_overlap=int(chunk_overlap),
                    chunk_separator=chunk_separator,
                    separator_is_regex=separator_is_regex,
                )
                if reset_before_ingest:
                    st.session_state.pop("results", None)
                    st.session_state.pop("selected_index", None)
                st.success(f"取り込み完了: {stats.documents} 文書 / {stats.chunks} チャンク")
            except Exception as exc:
                show_error("文書取り込みに失敗しました。ChromaDB と Ollama の起動、embeddinggemma の pull 状態を確認してください。", exc)

    if st.button("ChromaDBをリセット", use_container_width=True):
        try:
            get_chroma_client().reset_collection()
            st.session_state.pop("results", None)
            st.session_state.pop("selected_index", None)
            st.success("ChromaDB collection をリセットしました。")
        except Exception as exc:
            show_error("ChromaDB のリセットに失敗しました。", exc)

    if st.button("接続確認", use_container_width=True):
        try:
            get_chroma_client().verify()
            get_ollama_client().embed("connection test")
            st.success("ChromaDB と Ollama に接続できました。")
        except Exception as exc:
            show_error("接続確認に失敗しました。", exc)

    st.header("接続設定")
    st.caption(f"ChromaDB: `{os.getenv('CHROMA_HOST', 'chromadb')}:{os.getenv('CHROMA_PORT', '8000')}`")
    st.caption(f"Ollama: `{os.getenv('OLLAMA_URL', 'http://ollama:11434')}`")
    st.caption(f"Embedding: `{os.getenv('EMBEDDING_MODEL', 'embeddinggemma')}`")
    st.caption(f"Collection: `{os.getenv('COLLECTION_NAME', 'document_chunks')}`")
    st.caption(f"Docs: `{os.getenv('DOCS_DIR', '/app/docs')}`")

query = st.text_input("検索文", placeholder="例: 憲法改正の議論、反乱軍の作戦")
if st.button("検索実行", type="primary"):
    if not query.strip():
        st.warning("検索文を入力してください。")
    else:
        with st.spinner("検索文を Embedding 化し、ChromaDB で検索しています..."):
            try:
                st.session_state["results"] = search(query, top_k)
                st.session_state["selected_index"] = 0
            except Exception as exc:
                show_error("検索に失敗しました。先に文書取り込みを実行しているか確認してください。", exc)
                st.session_state["results"] = []

results = st.session_state.get("results", [])

if not results:
    st.info("文書を取り込んだあと、検索文を入力して「検索実行」を押してください。")
    st.stop()

st.subheader("検索結果一覧")
labels = [
    (
        f"{index + 1}. {row['metadata'].get('title', 'Untitled')} / "
        f"{row['metadata'].get('path', '')} / "
        f"Chunk {row['metadata'].get('chunk_index', '')} / "
        f"distance={format_number(row['distance'])}"
    )
    for index, row in enumerate(results)
]
selected_index = st.selectbox(
    "選択チャンク",
    range(len(results)),
    format_func=lambda index: labels[index],
    key="selected_index",
)
selected = results[selected_index]

for index, row in enumerate(results, start=1):
    metadata = row["metadata"]
    with st.container(border=True):
        st.markdown(f"**{index}. {metadata.get('title', 'Untitled')}**")
        st.caption(
            f"`{metadata.get('path', '')}` / Chunk {metadata.get('chunk_index', '')} / "
            f"distance={format_number(row['distance'])} / score={format_number(row['score'])}"
        )
        st.write(row["document"])

detail_col, graph_col = st.columns([1, 1.25], gap="large")

with detail_col:
    st.subheader("選択チャンク詳細")
    metadata = selected["metadata"]
    st.markdown(f"**{metadata.get('title', 'Untitled')}**")
    st.caption(
        f"`{metadata.get('path', '')}` / Chunk {metadata.get('chunk_index', '')} / "
        f"source_type={metadata.get('source_type', '')}"
    )
    st.metric("distance", format_number(selected["distance"]))
    st.metric("score", format_number(selected["score"]))
    st.write(selected["document"])

with graph_col:
    st.subheader("仮想グラフビュー")
    graph_data = build_virtual_graph(results, similarity_threshold=similarity_threshold)
    st.caption(
        f"検索結果 {len(graph_data['nodes'])} ノード、"
        f"類似度 {similarity_threshold:.2f} 以上の仮想エッジ {len(graph_data['edges'])} 本を表示します。"
    )
    components.html(build_graph_html(graph_data), height=680, scrolling=True)
