"""ナレッジ管理（Gemini Gem経由のナレッジ蓄積）"""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme

apply_minimal_theme()

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)

INPUT_ANALYZED_PATH = Path(__file__).parent.parent / "data" / "input_analyzed.json"

st.title("📚 ナレッジ蓄積")
st.caption("X投稿・記事URL・本などからGemini Gemで構造化したナレッジを保存します。")

tab_list, tab_input, tab_add = st.tabs(["📋 一覧", "🔍 Notionインプット分析", "➕ 新規追加"])

with tab_input:
    st.markdown("### Notionインプット分析結果")
    st.caption("/input-analyze を実行すると、インプットDBの未処理レコードを分析してここに蓄積されます。")

    if not INPUT_ANALYZED_PATH.exists() or INPUT_ANALYZED_PATH.read_text().strip() in ("", "[]"):
        st.info("まだ分析結果がありません。Claude Code で `/input-analyze` を実行してください。")
    else:
        records = json.loads(INPUT_ANALYZED_PATH.read_text(encoding="utf-8"))

        # フィルタ
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_note = st.selectbox("Noteプロジェクト", ["すべて", "3", "2", "1"], key="f_note")
        with col2:
            filter_career = st.selectbox("キャリア・仕事", ["すべて", "3", "2", "1"], key="f_career")
        with col3:
            filter_idea = st.selectbox("発信アイデア", ["すべて", "3", "2", "1"], key="f_idea")

        search_q = st.text_input("🔍 タイトル・タグ検索", placeholder="キーワードを入力")

        filtered = records
        if filter_note != "すべて":
            filtered = [r for r in filtered if r.get("scores", {}).get("note_project") >= int(filter_note)]
        if filter_career != "すべて":
            filtered = [r for r in filtered if r.get("scores", {}).get("career") >= int(filter_career)]
        if filter_idea != "すべて":
            filtered = [r for r in filtered if r.get("scores", {}).get("idea") >= int(filter_idea)]
        if search_q:
            q = search_q.lower()
            filtered = [
                r for r in filtered
                if q in r.get("title", "").lower()
                or any(q in t.lower() for t in r.get("tags", []))
                or q in r.get("memo", "").lower()
            ]

        st.caption(f"{len(filtered)} 件 / 全 {len(records)} 件")

        SCORE_LABEL = {3: "◎ 直接使える", 2: "○ 使える", 1: "△ 参考程度"}
        SCORE_COLOR = {3: "#e53935", 2: "#1e88e5", 1: "#43a047"}  # ◎赤 ○青 △緑

        def score_badge(score):
            label = SCORE_LABEL.get(score, "-")
            color = SCORE_COLOR.get(score, "#888")
            return f'<span style="color:{color};font-size:1.5em;font-weight:600">{label}</span>'

        for r in filtered:
            scores = r.get("scores", {})
            tags = r.get("tags", [])
            with st.expander(f"**{r.get('title', '(タイトルなし)')}**　{' '.join(f'#{t}' for t in tags)}"):
                if r.get("url"):
                    st.caption(f"🔗 [{r['url']}]({r['url']})")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("Noteプロジェクト", unsafe_allow_html=False)
                    st.markdown(score_badge(scores.get("note_project", 0)), unsafe_allow_html=True)
                with c2:
                    st.markdown("キャリア・仕事", unsafe_allow_html=False)
                    st.markdown(score_badge(scores.get("career", 0)), unsafe_allow_html=True)
                with c3:
                    st.markdown("発信アイデア", unsafe_allow_html=False)
                    st.markdown(score_badge(scores.get("idea", 0)), unsafe_allow_html=True)
                if r.get("memo"):
                    st.markdown(f"> {r['memo']}")
                st.caption(f"分析日: {r.get('analyzed_at', '')}　カテゴリ: {r.get('category', '')}")

with tab_add:
    st.markdown("### Gemini Gemの出力を貼り付け")
    st.caption("[Gemini プロンプトはこちら](Note/01_プロンプト/Gemini_ナレッジ取り込み.md)")
    with st.form("add_knowledge", clear_on_submit=True):
        title = st.text_input("タイトル *", placeholder="記事の核心を表すタイトル")
        category = st.selectbox(
            "カテゴリ",
            ["マーケティング", "マネジメント", "心理学", "SNS", "AI", "ロジカルシンキング", "その他"],
        )
        body = st.text_area("Geminiの出力（セクション2）", height=400, placeholder="## タイトル\n\n### 概要\n...")
        ref_url = st.text_input("参照元URL", placeholder="https://...")
        submitted = st.form_submit_button("💾 保存", type="primary")

        if submitted:
            if not title.strip() or not body.strip():
                st.error("タイトルと本文は必須です")
            else:
                from datetime import datetime
                ts = datetime.now().strftime("%Y%m%d_%H%M")
                safe_title = "".join(c for c in title if c.isalnum() or c in "あ-んア-ン一-龯ぁ-ゔー").strip()[:40]
                fname = f"{ts}_{category}_{safe_title}.md"
                content = f"""---
title: {title}
category: {category}
ref: {ref_url}
saved_at: {datetime.now().isoformat()}
---

{body}
"""
                (KNOWLEDGE_DIR / fname).write_text(content, encoding="utf-8")
                st.success(f"保存しました：{fname}")

with tab_list:
    files = sorted(KNOWLEDGE_DIR.glob("*.md"), reverse=True)
    if not files:
        st.info("まだナレッジがありません。新規追加から登録してください。")
    else:
        # カテゴリフィルタ
        all_cats = ["すべて", "マーケティング", "マネジメント", "心理学", "SNS", "AI", "ロジカルシンキング", "その他"]
        filter_cat = st.selectbox("カテゴリで絞り込み", all_cats)

        # 検索ボックス
        search_q = st.text_input("🔍 検索（タイトル・本文）", placeholder="キーワードを入力")

        st.caption(f"{len(files)} 件のナレッジ")
        for f in files:
            text = f.read_text(encoding="utf-8")
            # フィルタ
            if filter_cat != "すべて" and f"category: {filter_cat}" not in text:
                continue
            if search_q and search_q.lower() not in text.lower():
                continue

            # フロントマターから情報抽出
            lines = text.split("\n")
            meta = {}
            in_meta = False
            body_start = 0
            for i, line in enumerate(lines):
                if line.strip() == "---":
                    if not in_meta:
                        in_meta = True
                    else:
                        body_start = i + 1
                        break
                elif in_meta and ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()

            with st.expander(f"**{meta.get('title', f.stem)}** — {meta.get('category', '')}"):
                if meta.get("ref"):
                    st.caption(f"🔗 [参照元]({meta['ref']})")
                st.markdown("\n".join(lines[body_start:]))
