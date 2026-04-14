"""設定・FBレビュー"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme

st.set_page_config(page_title="設定 | Note執筆アシスタント", page_icon="⚙️", layout="wide")
apply_minimal_theme()

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

st.title("⚙️ 設定・プロンプト管理")
st.caption("プロンプトの編集・FBレビュー（後日実装予定の差分蓄積機能あり）")

tab_prompts, tab_fb = st.tabs(["📜 プロンプト編集", "💬 FBレビュー（準備中）"])

with tab_prompts:
    st.markdown("### プロンプトファイル一覧")
    prompt_files = sorted(PROMPTS_DIR.glob("*.md"))

    if not prompt_files:
        st.info("プロンプトファイルが見つかりません")
    else:
        selected = st.selectbox("編集するプロンプト", [f.name for f in prompt_files])
        if selected:
            target = PROMPTS_DIR / selected
            current_content = target.read_text(encoding="utf-8")

            edited = st.text_area("内容", value=current_content, height=600)

            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button("💾 保存", type="primary"):
                    target.write_text(edited, encoding="utf-8")
                    st.success(f"{selected} を保存しました")

with tab_fb:
    st.info("**準備中の機能**\n\n良かった記事を登録 → 改善前後の差分を蓄積 → プロンプト改善に反映する仕組み。\n\n優先度7番として実装予定。")
