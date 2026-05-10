"""ランディングページ（ホーム）"""
import json
import sys
from datetime import datetime, timedelta
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
st.markdown("左サイドバーから機能を選んでください。初めて使う / 使い方を確認したいときは **📖 ガイド** をどうぞ。")

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
    st.metric("📅 今月の投稿", f"{this_month_count} 本", "目標 6本")

st.divider()

# ── 今日のタスク ──
st.markdown("### 📋 今日のタスク")

_today = datetime.now().date()
_eom = (datetime(_today.year + (_today.month // 12), (_today.month % 12) + 1, 1) - timedelta(days=1)).date()
_days_until_eom = (_eom - _today).days
GOAL_ARTICLES = 6

_reminders = []

# インプットDB処理チェック
_analyzed_path = Path(__file__).parent / "data" / "input_analyzed.json"
if _analyzed_path.exists():
    _records = json.loads(_analyzed_path.read_text(encoding="utf-8"))
    if _records:
        _last_date = max(r.get("analyzed_at", "2000-01-01") for r in _records)
        _days_since = (_today - datetime.strptime(_last_date, "%Y-%m-%d").date()).days
        if _days_since >= 7:
            _reminders.append(("⚠️", f"インプットDB：前回処理から **{_days_since}日** 経過　→ `/input-analyze` を実行"))
        else:
            _reminders.append(("✅", f"インプットDB：前回処理 {_days_since}日前（次回は{7 - _days_since}日後）"))
    else:
        _reminders.append(("📥", "インプットDB：分析データなし　→ `/input-analyze` を実行"))
else:
    _reminders.append(("📥", "インプットDB：まだ分析なし　→ `/input-analyze` を実行"))

# 月末振り返りリマインド
if _days_until_eom <= 7:
    _reminders.append(("📝", f"月末まで **{_days_until_eom}日**　→ 振り返りドラフトの時期です"))

# 今月の投稿進捗
_remaining = max(GOAL_ARTICLES - this_month_count, 0)
if _remaining > 0:
    _reminders.append(("📊", f"今月の投稿：{this_month_count}本 / 目標{GOAL_ARTICLES}本　あと **{_remaining}本**"))
else:
    _reminders.append(("🎉", f"今月の投稿目標達成！（{this_month_count}本）"))

for _icon, _msg in _reminders:
    st.markdown(f"{_icon} &nbsp; {_msg}", unsafe_allow_html=True)

st.divider()

# ── ナビゲーション ──
st.markdown("### 🧭 ナビゲーション")

cols = st.columns(2)
with cols[0]:
    st.markdown("""
    **🎤 録音準備**
    テーマからアジェンダ・問いかけ・視点を生成。録音前のカンペ作成。音声が既にある場合は不要。

    **📝 執筆**
    新しい記事を書く。文字起こしから公開・SNS展開まで全9ステップ。

    **💡 アイデア**
    記事ネタの管理。Notionと同期。
    """)

with cols[1]:
    st.markdown("""
    **📚 ナレッジ**
    Gemini Gem経由のナレッジを蓄積・検索。

    **📊 KPI**
    月間目標と進捗の管理。

    **🔁 リバイバル**
    過去記事を切り取ってX投稿。新記事を書けない日の発信維持。

    **⚙️ 設定**
    プロンプトの編集・管理。
    """)

st.divider()

st.markdown("### 🎯 今月の目標（5月）")
st.markdown("""
- フォロワー：**75名**（累計目標、進捗はKPI画面で）
- 月間投稿：**6本**（週1〜1.5本ペース）
- 有料記事：**3本**公開
""")
