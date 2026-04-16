"""アイデア・ネタ管理"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme
from lib.notion import fetch_ideas, add_idea
from lib.state import init_write_state, reset_write_state

apply_minimal_theme()

st.title("💡 アイデア・ネタ管理")
st.caption("Notionの「Note投稿用」DBから、ステータスが『アイデア』の項目を表示します。")

tab_list, tab_add = st.tabs(["📋 一覧", "➕ 新規追加"])

with tab_list:
    if st.button("🔄 Notionから再読み込み"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Notionから取得中..."):
        ideas, err = fetch_ideas()

    if err:
        st.error(err)
    elif not ideas:
        st.info("アイデアがまだありません。「新規追加」タブから追加してください。")
    else:
        st.caption(f"{len(ideas)} 件のアイデア")
        for idea in ideas:
            with st.container():
                st.markdown(
                    f"""<div class="card">
                        <div class="card-title">{idea['title']}</div>
                        <div class="card-meta">{idea['memo'] or '（メモなし）'}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                c1, c2, _ = st.columns([1, 1, 4])
                with c1:
                    if st.button("✏️ 執筆する", key=f"write_{idea['id']}"):
                        init_write_state()
                        reset_write_state()
                        st.session_state.article_title = idea["title"]
                        st.session_state.transcription = f"【元アイデア】\n{idea['title']}\n{idea['memo']}\n\n（ここに音声録音の文字起こしを貼り付け）"
                        st.session_state.step = 0
                        st.switch_page("pages/1_📝_執筆.py")
                with c2:
                    if idea["url"]:
                        st.link_button("🔗 Notion", idea["url"])

with tab_add:
    st.markdown("### 新しいアイデアを追加")
    with st.form("add_idea_form", clear_on_submit=True):
        new_title = st.text_input("タイトル *", placeholder="例：INFJが朝起きられない本当の理由")
        new_memo = st.text_area("メモ", height=120, placeholder="どんな切り口で書きたいか、参考にした体験など")
        new_ref = st.text_input("参考URL", placeholder="https://...")
        submitted = st.form_submit_button("💾 Notionに追加", type="primary")

        if submitted:
            if not new_title.strip():
                st.error("タイトルは必須です")
            else:
                ok, msg = add_idea(new_title.strip(), new_memo.strip(), new_ref.strip())
                if ok:
                    st.success(msg)
                    st.cache_data.clear()
                else:
                    st.error(msg)
