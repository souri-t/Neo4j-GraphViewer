import streamlit as st


st.set_page_config(page_title="ChromaDB + Ollama 文書検索デモ", layout="wide")

pages = [
    st.Page("search_page.py", title="検索・グラフビュー"),
    st.Page("registration_page.py", title="文書登録"),
]

selected_page = st.navigation(pages)
selected_page.run()
