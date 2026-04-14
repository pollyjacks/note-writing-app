"""KPI・進捗管理"""
import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme
from lib.notion import fetch_published

st.set_page_config(page_title="KPI | Note執筆アシスタント", page_icon="📊", layout="wide")
apply_minimal_theme()

KPI_FILE = Path(__file__).parent.parent / "outputs" / "kpi_history.json"

# 目標値（マイルストーンより）
GOAL_FOLLOWERS = 100
GOAL_ARTICLES = 30
GOAL_PAID = 3

st.title("📊 KPI・進捗管理")

# 投稿済み記事数を取得
with st.spinner("Notionから投稿済みを取得中..."):
    published, err = fetch_published()

if err:
    st.warning(f"Notion取得失敗：{err}")
    published = []

# 今月の投稿数を計算
this_month = datetime.now().strftime("%Y-%m")
this_month_count = sum(1 for p in published if p.get("date", "").startswith(this_month))
total_count = len(published)

# ── サマリーカード ──
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("累計記事", f"{total_count}本")
with col2:
    st.metric("今月の投稿", f"{this_month_count}本", f"目標 {GOAL_ARTICLES}本")
with col3:
    progress_articles = min(this_month_count / GOAL_ARTICLES, 1.0)
    st.metric("月間進捗", f"{int(progress_articles * 100)}%")
with col4:
    st.metric("有料記事", "—", f"目標 {GOAL_PAID}本")

st.progress(progress_articles)
st.caption(f"今月の目標まであと **{max(GOAL_ARTICLES - this_month_count, 0)}本**")

st.divider()

# ── 月次数値入力 ──
st.markdown("### 📝 月次数値の入力")
st.caption("Note管理画面からコピペ → 自動保存されます")

# 既存データ読み込み
if KPI_FILE.exists():
    history = json.loads(KPI_FILE.read_text(encoding="utf-8"))
else:
    history = {}

with st.form("kpi_input"):
    target_month = st.text_input("対象月", value=this_month, placeholder="2026-04")
    existing = history.get(target_month, {})

    c1, c2 = st.columns(2)
    with c1:
        followers = st.number_input("フォロワー数", min_value=0, value=existing.get("followers", 0), step=1)
        likes = st.number_input("月間Like数", min_value=0, value=existing.get("likes", 0), step=1)
    with c2:
        views = st.number_input("月間流入数", min_value=0, value=existing.get("views", 0), step=1)
        revenue = st.number_input("有料記事売上（円）", min_value=0, value=existing.get("revenue", 0), step=100)

    note = st.text_area("メモ・気づき", value=existing.get("note", ""), height=100)

    if st.form_submit_button("💾 保存", type="primary"):
        history[target_month] = {
            "followers": followers,
            "likes": likes,
            "views": views,
            "revenue": revenue,
            "note": note,
            "updated_at": datetime.now().isoformat(),
        }
        KPI_FILE.parent.mkdir(exist_ok=True)
        KPI_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        st.success(f"{target_month} のデータを保存しました")
        st.rerun()

st.divider()

# ── 履歴 ──
st.markdown("### 📈 履歴")
if history:
    sorted_months = sorted(history.keys(), reverse=True)
    import pandas as pd
    df_data = []
    for m in sorted_months:
        d = history[m]
        df_data.append({
            "月": m,
            "フォロワー": d.get("followers", 0),
            "Like": d.get("likes", 0),
            "流入": d.get("views", 0),
            "売上": d.get("revenue", 0),
        })
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("まだ履歴がありません")

st.divider()

# ── 投稿済みカレンダー ──
st.markdown("### 📅 投稿済み一覧（直近）")
if published:
    sorted_pub = sorted(published, key=lambda p: p.get("date", ""), reverse=True)[:20]
    for p in sorted_pub:
        st.markdown(
            f"""<div class="card">
                <div class="card-title">{p['title']}</div>
                <div class="card-meta">📅 {p['date'] or '日付なし'} {' · 🔗 ' + p['url'] if p['url'] else ''}</div>
            </div>""",
            unsafe_allow_html=True,
        )
else:
    st.info("Notionから投稿済み記事を取得できませんでした")

st.divider()

# ── 保存済みアイキャッチ ──
st.markdown("### 🖼️ 保存済みアイキャッチ")
EYECATCH_DIR = Path(__file__).parent.parent / "eyecatches"
if EYECATCH_DIR.exists():
    images = sorted(EYECATCH_DIR.glob("*"), reverse=True)
    images = [img for img in images if img.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    if images:
        st.caption(f"{len(images)} 枚の画像")
        cols = st.columns(3)
        for i, img in enumerate(images[:12]):
            with cols[i % 3]:
                st.image(str(img), caption=img.stem, use_container_width=True)
    else:
        st.info("まだアイキャッチが保存されていません")
else:
    st.info("アイキャッチフォルダがありません")
