import os
from pathlib import Path

import streamlit as st

from ingest import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SEPARATOR_DISPLAY, DEFAULT_CHUNK_SIZE, MAX_CHUNK_SIZE, ingest_docs
from ui_common import get_chroma_client, get_ollama_client, show_error


def list_dataset_dirs(docs_root: Path) -> list[Path]:
    if not docs_root.exists():
        return []
    return sorted((path for path in docs_root.iterdir() if path.is_dir()), key=lambda path: path.name)


st.title("文書登録")

docs_root = Path(os.getenv("DOCS_DIR", "/app/docs"))
dataset_dirs = list_dataset_dirs(docs_root)
dataset_names = [path.name for path in dataset_dirs]

st.subheader("データセット")
if dataset_names:
    selected_dataset = st.selectbox("登録するデータセット", dataset_names)
    selected_docs_dir = docs_root / selected_dataset
else:
    selected_dataset = ""
    selected_docs_dir = docs_root
    st.warning(f"`{docs_root}` 配下にデータセットフォルダが見つかりません。")

db_status_placeholder = st.empty()

st.subheader("チャンク設定")
chunk_separator = st.text_input("チャンク区切り文字", value=DEFAULT_CHUNK_SEPARATOR_DISPLAY)
separator_is_regex = st.checkbox("正規表現として扱う", value=False)

chunk_col, overlap_col = st.columns([1, 1])
with chunk_col:
    chunk_size = st.number_input(
        "最大チャンク長（文字数）",
        min_value=1,
        max_value=MAX_CHUNK_SIZE,
        value=DEFAULT_CHUNK_SIZE,
        step=50,
    )
with overlap_col:
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

st.subheader("登録操作")
action_col, reset_col, connection_col = st.columns([1, 1, 1])

with action_col:
    if st.button("文書を取り込む", type="primary", use_container_width=True, disabled=not bool(selected_dataset)):
        with st.spinner(f"{selected_dataset} 配下の .md を読み込み、Embedding を ChromaDB に保存しています..."):
            try:
                stats = ingest_docs(
                    docs_dir=selected_docs_dir,
                    dataset_name=selected_dataset,
                    reset=reset_before_ingest,
                    chunk_size=int(chunk_size),
                    chunk_overlap=int(chunk_overlap),
                    chunk_separator=chunk_separator,
                    separator_is_regex=separator_is_regex,
                )
                if reset_before_ingest:
                    st.session_state.pop("results", None)
                    st.session_state.pop("selected_index", None)
                st.success(f"取り込み完了: {selected_dataset} / {stats.documents} 文書 / {stats.chunks} チャンク")
            except Exception as exc:
                show_error("文書取り込みに失敗しました。ChromaDB と Ollama の起動、embeddinggemma の pull 状態を確認してください。", exc)

with reset_col:
    if st.button("ChromaDBをリセット", use_container_width=True):
        try:
            get_chroma_client().reset_collection()
            st.session_state.pop("results", None)
            st.session_state.pop("selected_index", None)
            st.success("ChromaDB collection をリセットしました。")
        except Exception as exc:
            show_error("ChromaDB のリセットに失敗しました。", exc)

with connection_col:
    if st.button("接続確認", use_container_width=True):
        try:
            get_chroma_client().verify()
            get_ollama_client().embed("connection test")
            st.success("ChromaDB と Ollama に接続できました。")
        except Exception as exc:
            show_error("接続確認に失敗しました。", exc)

st.subheader("接続設定")
st.caption(f"ChromaDB: `{os.getenv('CHROMA_HOST', 'chromadb')}:{os.getenv('CHROMA_PORT', '8000')}`")
st.caption(f"Ollama: `{os.getenv('OLLAMA_URL', 'http://ollama:11434')}`")
st.caption(f"Embedding: `{os.getenv('EMBEDDING_MODEL', 'embeddinggemma')}`")
st.caption(f"Collection: `{os.getenv('COLLECTION_NAME', 'document_chunks')}`")
st.caption(f"Docs: `{os.getenv('DOCS_DIR', '/app/docs')}`")

try:
    db_status_placeholder.caption(f"現在のDB: `{get_chroma_client().describe_datasets()}`")
except Exception as exc:
    db_status_placeholder.caption("現在のDB: `取得できません`")
