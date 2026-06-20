import streamlit as st

st.set_page_config(page_title="Neo4j + Ollama 文書検索デモ", layout="wide")

pages = [
    st.Page("search_page.py", title="意味検索"),
    st.Page("detail_graph_page.py", title="詳細・グラフビュー"),
]

selected_page = st.navigation(pages)
selected_page.run()
