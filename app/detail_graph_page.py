import streamlit as st
import streamlit.components.v1 as components

from graph_view import build_graph_html
from ui_common import get_neo4j_client, render_sidebar, search_controls, select_result, show_error


st.title("詳細・グラフビュー")
render_sidebar()

st.subheader("検索")
query, _, results = search_controls("detail_page")
selected = select_result(results, "detail_page") if results else None

if not selected and query:
    st.info("検索結果がありません。文書取り込み後に別の検索文を試してください。")
elif not selected:
    st.info("検索文を入力して、グラフ表示する Chunk を選択してください。")
    st.stop()

selected_chunk_id = selected["chunk_id"]

st.subheader("詳細")
st.markdown(f"**{selected['title']}**")
st.caption(f"`{selected['path']}` / Chunk {selected['chunk_index']} / score={selected['score']:.4f}")
with st.expander("選択 Chunk 本文", expanded=True):
    st.write(selected["text"])

st.subheader("グラフビュー")
try:
    graph_data = get_neo4j_client().graph_context(selected_chunk_id)
    if graph_data["nodes"]:
        components.html(build_graph_html(graph_data), height=720, scrolling=True)
    else:
        st.info("グラフデータが見つかりませんでした。")
except Exception as exc:
    show_error("グラフビューの取得に失敗しました。", exc)
