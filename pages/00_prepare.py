"""録音準備（アジェンダ・問いかけ生成）"""
from datetime import datetime
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme
from lib.state import load_prompt, init_write_state, reset_write_state, OUTPUTS_DIR

apply_minimal_theme()

PREPARE_DIR = OUTPUTS_DIR / "prepare"
PREPARE_DIR.mkdir(exist_ok=True)

DEFAULTS = {
    "prepare_theme": "",
    "prepare_memo": "",
    "prepare_result": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


st.title("🎤 録音準備")
st.caption("録音する前に、テーマからアジェンダ・問いかけ・視点を生成します。音声がすでにある場合は使わずに直接「執筆」へ進んでください。")

st.info("使い方：① テーマ入力 → ② Claude.aiでプロンプト実行 → ③ 回答を貼り戻し → ④ それを見ながらiPhoneで録音")

st.divider()

# ── Step 1: テーマ入力 ──────────────────────────────────────────────
st.markdown("### ① テーマ入力")
theme = st.text_input(
    "今回のテーマ *",
    value=st.session_state.prepare_theme,
    placeholder="例：INFJが朝起きられない本当の理由",
)
memo = st.text_area(
    "補足メモ（任意）",
    value=st.session_state.prepare_memo,
    height=120,
    placeholder="切り口の案、思い出した体験、参考にしたい視点など",
)

if theme != st.session_state.prepare_theme:
    st.session_state.prepare_theme = theme
if memo != st.session_state.prepare_memo:
    st.session_state.prepare_memo = memo

st.divider()

# ── Step 2: プロンプト表示 ──────────────────────────────────────────
st.markdown("### ② Claude.ai用プロンプト")
if not theme.strip():
    st.caption("👆 テーマを入力すると、プロンプトが表示されます。")
else:
    prompt = load_prompt("00_agenda.md", theme=theme, memo=memo or "（なし）")
    st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付けてください。</div>', unsafe_allow_html=True)
    with st.expander("📋 プロンプトを表示", expanded=True):
        st.code(prompt, language=None)

st.divider()

# ── Step 3: 回答貼り戻し ────────────────────────────────────────────
st.markdown("### ③ Claudeの回答を貼り戻し")
result = st.text_area(
    "アジェンダ・問いかけ・視点",
    value=st.session_state.prepare_result,
    height=420,
    placeholder="Claude.aiからの回答をそのまま貼り付け",
)
if result != st.session_state.prepare_result:
    st.session_state.prepare_result = result

st.divider()

# ── Step 4: アクション ─────────────────────────────────────────────
st.markdown("### ④ 次のアクション")
st.caption("このアジェンダを見ながらiPhoneで録音してください。必要に応じて保存・執筆画面への引き継ぎができます。")

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("💾 このアジェンダを保存", disabled=not result.strip(), use_container_width=True):
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        safe = "".join(c for c in theme if c.isalnum() or c in "あ-んア-ン一-龯ぁ-ゔー_- ")[:40].strip() or "untitled"
        fpath = PREPARE_DIR / f"{ts}_{safe}.md"
        fpath.write_text(
            f"# {theme}\n\n**作成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n## 補足メモ\n{memo or '（なし）'}\n\n---\n\n{result}\n",
            encoding="utf-8",
        )
        st.success(f"保存しました：{fpath.name}")

with c2:
    if st.button("📝 このテーマで執筆へ", type="primary", disabled=not theme.strip(), use_container_width=True):
        init_write_state()
        reset_write_state()
        st.session_state.article_title = theme
        st.session_state.step = 0
        st.switch_page("pages/01_write.py")

with c3:
    if st.button("🔄 クリア", use_container_width=True):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.rerun()

st.divider()

# ── 保存済み一覧 ────────────────────────────────────────────────
st.markdown("### 📂 保存済みアジェンダ")
files = sorted(PREPARE_DIR.glob("*.md"), reverse=True)
if not files:
    st.caption("まだ保存済みのアジェンダはありません。")
else:
    st.caption(f"{len(files)} 件")
    for f in files[:10]:
        with st.expander(f.stem):
            st.markdown(f.read_text(encoding="utf-8"))
