import streamlit as st

from ui_common import render_sidebar, search_controls, select_result


st.title("Neo4j + Ollama 文書検索・グラフビューデモ")
render_sidebar()

st.subheader("意味検索")
query, _, results = search_controls("search_page")
if results:
    select_result(results, "search_page")
    st.info("詳細とグラフは左のページ一覧から「詳細・グラフビュー」を開いて確認できます。このページの選択結果も引き継がれます。")

    for index, row in enumerate(results, start=1):
        with st.container(border=True):
            st.markdown(f"**{index}. {row['title']}**")
            st.caption(f"`{row['path']}` / Chunk {row['chunk_index']} / 類似度 {row['score']:.4f}")
            st.write(row["text"])
elif query:
    st.info("検索結果がありません。文書取り込み後に別の検索文を試してください。")
else:
    st.info("検索文を入力すると、Neo4j のベクトルインデックスから近い Chunk を取得します。")
