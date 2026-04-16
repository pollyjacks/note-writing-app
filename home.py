"""ランディングページ（ホーム）"""
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from lib.theme import apply_minimal_theme
from lib.notion import fetch_ideas, fetch_published

apply_minimal_theme()

st.title("Note執筆アシスタント")
st.caption("INFJのための、執筆〜SNS展開までの統合ツール")

st.write("")
st.markdown("### 👋 ようこそ")
st.markdown("左サイドバーから機能を選んでください。")

st.write("")

# ── サマリーカード ──
col1, col2, col3 = st.columns(3)

with col1:
    with st.spinner("..."):
        ideas, _ = fetch_ideas()
    st.metric("💡 アイデア数", f"{len(ideas)} 件")
    st.caption("Notionに保存されているアイデア")

with col2:
    with st.spinner("..."):
        published, _ = fetch_published()
    st.metric("📚 投稿済み", f"{len(published)} 本")
    st.caption("Notionに登録されている投稿済み記事")

with col3:
    this_month = datetime.now().strftime("%Y-%m")
    this_month_count = sum(1 for p in published if p.get("date", "").startswith(this_month))
    st.metric("📅 今月の投稿", f"{this_month_count} 本", "目標 30本")

st.divider()

# ── ナビゲーション ──
st.markdown("### 🧭 ナビゲーション")

cols = st.columns(2)
with cols[0]:
    st.markdown("""
    **📝 執筆**
    新しい記事を書く。文字起こしから公開・SNS展開まで全8ステップ。

    **💡 アイデア**
    記事ネタの管理。Notionと同期。

    **📚 ナレッジ**
    Gemini Gem経由のナレッジを蓄積・検索。
    """)

with cols[1]:
    st.markdown("""
    **📊 KPI**
    月間目標と進捗の管理。

    **⚙️ 設定**
    プロンプトの編集・管理。
    """)

st.divider()

st.markdown("### 🎯 今月の目標")
st.markdown("""
- フォロワー：**100名**（現在の進捗はKPI画面で）
- 月間投稿：**30本**（無料27 + 有料3）
- 有料記事：**3本公開・購入発生**
""")
