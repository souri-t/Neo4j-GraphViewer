import streamlit as st
import streamlit.components.v1 as components

from graph_view import build_graph_html, build_virtual_graph
from ui_common import format_number, search_chunks, show_error


st.title("検索・仮想グラフビュー")

query = st.text_input("検索文", placeholder="例: 憲法改正の議論、反乱軍の作戦")
control_col, threshold_col = st.columns([1, 1])
with control_col:
    top_k = st.slider("TopK", min_value=3, max_value=30, value=10)
with threshold_col:
    similarity_threshold = st.slider("グラフ表示用の類似度閾値", min_value=0.0, max_value=1.0, value=0.78, step=0.01)

if st.button("検索実行", type="primary"):
    if not query.strip():
        st.warning("検索文を入力してください。")
    else:
        with st.spinner("検索文を Embedding 化し、ChromaDB で検索しています..."):
            try:
                st.session_state["results"] = search_chunks(query, top_k)
                st.session_state["selected_index"] = 0
            except Exception as exc:
                show_error("検索に失敗しました。先に文書取り込みを実行しているか確認してください。", exc)
                st.session_state["results"] = []

results = st.session_state.get("results", [])

if not results:
    st.info("文書登録ページで文書を取り込んだあと、検索文を入力して「検索実行」を押してください。")
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
