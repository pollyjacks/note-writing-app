"""Note執筆アシスタント — メインエントリ（サイドバーナビゲーション）"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from lib.theme import apply_minimal_theme

st.set_page_config(
    page_title="Note執筆アシスタント",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_minimal_theme()

# st.navigation でページを定義（日本語+絵文字タイトル）
pages = [
    st.Page("home.py", title="ホーム", icon="🏠", default=True),
    st.Page("pages/07_guide.py", title="ガイド", icon="📖"),
    st.Page("pages/00_prepare.py", title="録音準備", icon="🎤"),
    st.Page("pages/01_write.py", title="執筆", icon="📝"),
    st.Page("pages/02_ideas.py", title="アイデア", icon="💡"),
    st.Page("pages/03_knowledge.py", title="ナレッジ", icon="📚"),
    st.Page("pages/04_kpi.py", title="KPI", icon="📊"),
    st.Page("pages/06_revival.py", title="リバイバル", icon="🔁"),
    st.Page("pages/08_paid.py", title="有料記事", icon="💴"),
    st.Page("pages/05_settings.py", title="設定", icon="⚙️"),
]

nav = st.navigation(pages)
nav.run()
