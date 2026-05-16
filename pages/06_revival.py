"""過去記事リバイバル：Xで切り取って再拡散する投稿文生成"""
from datetime import date, datetime
from pathlib import Path
import sys

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme
from lib.state import load_prompt, OUTPUTS_DIR
from lib.revival import load_all_posts, enrich_with_notion, score_post, suggest_today

apply_minimal_theme()

REVIVAL_DIR = OUTPUTS_DIR / "revival"
REVIVAL_DIR.mkdir(exist_ok=True)

DEFAULTS = {
    "revival_selected_path": "",
    "revival_prompt_shown": False,
    "revival_result": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


st.title("🔁 過去記事リバイバル")
st.caption("過去記事を「もとやま式つまみ食い」でXに切り取って投稿。新記事を書けない日でも発信を継続できます。")

today = date.today()
today_str = today.strftime("%Y-%m-%d（%a）")

# ── 今日のおすすめ ────────────────────────────────────────────────
st.markdown("### 🎯 今日のおすすめ")
st.caption(f"今日: **{today_str}** の時期性（季節/曜日/経過日数）でスコア上位3本をサジェスト")

if st.button("🔄 候補を再計算", key="refresh_suggest"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("候補を計算中..."):
    top, err = suggest_today(top_n=3)

if err:
    st.warning(err)
elif not top:
    st.info("今日の時期性に合う候補が見つかりませんでした。下の一覧から手動で選んでください。")
else:
    cols = st.columns(len(top))
    for i, p in enumerate(top):
        with cols[i]:
            st.markdown(
                f"""<div class="card">
                    <div class="card-title">{p['title']}</div>
                    <div class="card-meta">スコア: <b>{p['score']}</b><br>{('<br>'.join(p['reasons']))}<br>📅 {p['date'] or '日付不明'}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("この記事で生成 →", key=f"pick_top_{i}", type="primary", use_container_width=True):
                st.session_state.revival_selected_path = p["path"]
                st.session_state.revival_result = ""
                st.rerun()

st.divider()

# ── 手動選択 ──────────────────────────────────────────────────
st.markdown("### 📚 一覧から選ぶ")

all_posts = enrich_with_notion(load_all_posts())
if not all_posts:
    st.warning("過去記事が見つかりません。")
    st.stop()

search_q = st.text_input("🔍 タイトル検索", placeholder="キーワードを入力")
filtered = [p for p in all_posts if not search_q or search_q.lower() in p["title"].lower()]
filtered.sort(key=lambda p: p.get("date", ""), reverse=True)

st.caption(f"{len(filtered)} 件 / 全 {len(all_posts)} 件")

# セレクトボックス形式
options = ["（選択してください）"] + [f"{p.get('date') or '----'}  |  {p['title']}" for p in filtered]
path_lookup = [""] + [p["path"] for p in filtered]

default_idx = 0
if st.session_state.revival_selected_path in path_lookup:
    default_idx = path_lookup.index(st.session_state.revival_selected_path)

choice_idx = st.selectbox(
    "記事を選択",
    range(len(options)),
    format_func=lambda i: options[i],
    index=default_idx,
    label_visibility="collapsed",
)

if choice_idx > 0:
    st.session_state.revival_selected_path = path_lookup[choice_idx]

st.divider()

# ── 選択中の記事 ───────────────────────────────────────────────
if not st.session_state.revival_selected_path:
    st.info("👆 記事を選択してください。")
    st.stop()

selected = next((p for p in all_posts if p["path"] == st.session_state.revival_selected_path), None)
if not selected:
    st.error("選択した記事が見つかりませんでした。")
    st.stop()

# スコアと理由を再計算して表示
sc, reasons = score_post(selected, today)
st.markdown(f"### 📝 選択中: {selected['title']}")
meta_parts = [f"📅 {selected['date'] or '日付不明'}"]
if selected["url"]:
    meta_parts.append(f"🔗 [Note]({selected['url']})")
meta_parts.append(f"📂 {selected['source']}")
st.caption(" · ".join(meta_parts))
st.caption(f"今日の時期性スコア: **{sc}**　（{'; '.join(reasons)}）")

with st.expander("📖 本文プレビュー（先頭3000字）", expanded=False):
    st.text(selected["body"][:3000])

st.divider()

# ── プロンプト生成 ─────────────────────────────────────────────
st.markdown("### 🤖 Claude.ai 用プロンプト")

url_for_prompt = selected["url"] or "（未設定）"
prompt = load_prompt(
    "09_x_revival.md",
    title=selected["title"],
    article=selected["body"][:8000],
    url=url_for_prompt,
    today=today_str,
)

st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付けてください。</div>', unsafe_allow_html=True)
with st.expander("📋 プロンプトを表示", expanded=True):
    st.code(prompt, language=None)

st.divider()

# ── 貼り戻し ──────────────────────────────────────────────────
st.markdown("### ✍️ Claudeの回答を貼り戻し")
result = st.text_area(
    "X投稿文（パターンA/B/C）",
    value=st.session_state.revival_result,
    height=420,
    placeholder="Claude.aiからの回答をそのまま貼り付け",
)
if result != st.session_state.revival_result:
    st.session_state.revival_result = result

st.divider()

# ── 保存 ──────────────────────────────────────────────────────
st.markdown("### 💾 保存")
st.caption("リバイバル履歴として保存しておくと、同じ記事を何度も切り取り直すときに便利です。")

c1, c2 = st.columns(2)
with c1:
    if st.button("💾 このリバイバルを保存", disabled=not result.strip(), type="primary", use_container_width=True):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe = "".join(c for c in selected["title"] if c.isalnum() or c in "あ-んア-ン一-龯ぁ-ゔー_- ")[:30].strip() or "untitled"
        fpath = REVIVAL_DIR / f"{ts}_{safe}.md"
        content = f"""# {selected['title']}（リバイバル）

**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**元記事**: {selected['path']}
**Note URL**: {selected['url'] or '（未設定）'}
**時期性スコア**: {sc}（{'; '.join(reasons)}）

---

{result}
"""
        fpath.write_text(content, encoding="utf-8")
        st.success(f"保存しました：{fpath.name}")

with c2:
    if st.button("🔄 別の記事を選ぶ", use_container_width=True):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.rerun()

# ── 保存済みリバイバル一覧 ─────────────────────────────────────
st.divider()
st.markdown("### 📂 保存済みリバイバル")
files = sorted(REVIVAL_DIR.glob("*.md"), reverse=True)
if not files:
    st.caption("まだ保存済みのリバイバルはありません。")
else:
    st.caption(f"{len(files)} 件")
    for f in files[:10]:
        with st.expander(f.stem):
            st.markdown(f.read_text(encoding="utf-8"))
