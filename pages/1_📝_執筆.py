"""執筆フロー（Step 0〜8）"""
from datetime import datetime
import sys
from pathlib import Path

import streamlit as st

# lib モジュールを import するためにパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme
from lib.state import init_write_state, reset_write_state, load_prompt, parse_titles, OUTPUTS_DIR, EYECATCH_DIR
from lib.notion import sync_to_notion, update_notion_url

st.set_page_config(page_title="執筆 | Note執筆アシスタント", page_icon="📝", layout="wide")
apply_minimal_theme()
init_write_state()


def go_to(step: int):
    st.session_state.step = step
    st.rerun()


def reset():
    reset_write_state()
    st.rerun()


STEPS = [
    "文字起こし入力",
    "① 要約プロンプト",
    "② 構成案プロンプト",
    "★ 構成案レビュー・タイトル選択",
    "③ 執筆（前半）",
    "④ 執筆（後半）",
    "⑤ 公開準備",
    "★ 最終レビュー・保存",
    "⑥ SNS展開（公開後）",
]
REVIEW_STEPS = {3, 7}

# ── ヘッダー ──────────────────────────────────────────────────────────────
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.title("📝 執筆フロー")
with col_reset:
    st.write("")
    if st.button("🔄 リセット", help="入力内容をすべてリセット"):
        reset()

step = st.session_state.step
is_review = step in REVIEW_STEPS

st.markdown(f'<div class="step-label">Step {step + 1} / {len(STEPS)}</div>', unsafe_allow_html=True)
if is_review:
    st.markdown(f'<div class="review-badge">⭐ {STEPS[step]} — あなたの確認が必要です</div>', unsafe_allow_html=True)
else:
    st.subheader(STEPS[step])
st.progress(step / (len(STEPS) - 1))
st.divider()

# ── STEP 0 ───────────────────────────────────────────────────────────────
if step == 0:
    st.info("iPhoneで文字起こしたテキストをそのまま貼り付けてください。")
    transcription = st.text_area(
        "文字起こしテキスト",
        value=st.session_state.transcription,
        height=420,
        placeholder="ここに文字起こしのテキストを貼り付けてください...",
        label_visibility="collapsed",
    )
    st.caption(f"文字数: {len(transcription.strip()):,} 文字")
    st.write("")
    if st.button("次へ → 要約プロンプト", type="primary", disabled=not transcription.strip(), use_container_width=True):
        st.session_state.transcription = transcription
        go_to(1)

# ── STEP 1 ───────────────────────────────────────────────────────────────
elif step == 1:
    st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付け、返答をここに貼り戻してください。</div>', unsafe_allow_html=True)
    prompt = load_prompt("01_summarize.md", transcription=st.session_state.transcription)
    with st.expander("📋 プロンプトを表示", expanded=True):
        st.code(prompt, language=None)
    st.write("")
    summary = st.text_area("Claudeの返答", value=st.session_state.summary, height=300, placeholder="要約・法則化・INFJペイン...")
    st.write("")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("← 戻る", use_container_width=True):
            go_to(0)
    with c2:
        if st.button("次へ → 構成案", type="primary", disabled=not summary.strip(), use_container_width=True):
            st.session_state.summary = summary
            go_to(2)

# ── STEP 2 ───────────────────────────────────────────────────────────────
elif step == 2:
    st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付け、返答をここに貼り戻してください。</div>', unsafe_allow_html=True)
    prompt = load_prompt("02_outline.md", transcription=st.session_state.transcription, summary=st.session_state.summary)
    with st.expander("📋 プロンプトを表示", expanded=True):
        st.code(prompt, language=None)
    st.write("")
    outline = st.text_area("Claudeの返答", value=st.session_state.outline, height=300, placeholder="タイトル案・構成案...")
    st.write("")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("← 戻る", use_container_width=True):
            go_to(1)
    with c2:
        if st.button("次へ → 構成案レビュー", type="primary", disabled=not outline.strip(), use_container_width=True):
            st.session_state.outline = outline
            go_to(3)

# ── STEP 3 ───────────────────────────────────────────────────────────────
elif step == 3:
    st.success("構成案を確認・修正し、タイトルを選択してから執筆を開始してください。")
    outline = st.text_area("構成案（直接編集できます）", value=st.session_state.outline, height=420)

    st.write("")
    st.markdown("### 📌 タイトル選択")
    parsed_titles = parse_titles(outline)
    if parsed_titles:
        st.caption(f"構成案から {len(parsed_titles)} 個のタイトル候補を検出しました。")
        options = parsed_titles + ["✏️ 自分で入力する"]
        default_idx = 0
        if st.session_state.article_title in parsed_titles:
            default_idx = parsed_titles.index(st.session_state.article_title)
        choice = st.radio("候補から選択", options, index=default_idx, label_visibility="collapsed")
        if choice == "✏️ 自分で入力する":
            selected_title = st.text_input(
                "カスタムタイトル",
                value=st.session_state.article_title if st.session_state.article_title not in parsed_titles else "",
                placeholder="タイトルを入力",
            )
        else:
            selected_title = choice
    else:
        st.caption("タイトル候補を自動検出できませんでした。")
        selected_title = st.text_input("タイトル", value=st.session_state.article_title, placeholder="タイトルを入力")

    st.write("")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("← 戻って修正", use_container_width=True):
            st.session_state.outline = outline
            st.session_state.article_title = selected_title
            go_to(2)
    with c2:
        if st.button("✅ この構成案で執筆を開始", type="primary", disabled=not (selected_title or "").strip(), use_container_width=True):
            st.session_state.outline = outline
            st.session_state.article_title = selected_title
            go_to(4)

# ── STEP 4 ───────────────────────────────────────────────────────────────
elif step == 4:
    st.markdown('<div class="copy-hint">👇 以下の2つのプロンプトを<strong>順番に</strong> Claude.ai に送ってください。</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["プロンプト1: 内容の読み込み", "プロンプト2: 前半の執筆"])
    with tab1:
        prompt_setup = load_prompt(
            "03_write_setup.md",
            transcription=st.session_state.transcription,
            summary=st.session_state.summary,
            outline=st.session_state.outline,
        )
        st.code(prompt_setup, language=None)
    with tab2:
        st.code(load_prompt("04_write_first_half.md"), language=None)
    st.write("")
    article_first = st.text_area("前半の執筆結果", value=st.session_state.article_first, height=350)
    st.write("")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("← 戻る", use_container_width=True):
            go_to(3)
    with c2:
        if st.button("次へ → 後半", type="primary", disabled=not article_first.strip(), use_container_width=True):
            st.session_state.article_first = article_first
            go_to(5)

# ── STEP 5 ───────────────────────────────────────────────────────────────
elif step == 5:
    st.markdown('<div class="copy-hint">👇 前半を書いたClaude.aiの会話を<strong>続けて</strong>、以下のプロンプトを送ってください。</div>', unsafe_allow_html=True)
    with st.expander("📋 プロンプトを表示", expanded=True):
        st.code(load_prompt("05_write_second_half.md"), language=None)
    st.write("")
    article_second = st.text_area("後半の執筆結果", value=st.session_state.article_second, height=350)
    st.write("")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("← 戻る", use_container_width=True):
            go_to(4)
    with c2:
        if st.button("次へ → 公開準備", type="primary", disabled=not article_second.strip(), use_container_width=True):
            st.session_state.article_second = article_second
            go_to(6)

# ── STEP 6 ───────────────────────────────────────────────────────────────
elif step == 6:
    st.info("Note公開用のアイキャッチプロンプト・ハッシュタグ・マガジン提案を生成します。")
    full_article = f"{st.session_state.article_first}\n\n{st.session_state.article_second}"
    prompt = load_prompt("07_publish_prep.md", title=st.session_state.article_title or "（未設定）", article=full_article)
    st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付けてください。</div>', unsafe_allow_html=True)
    with st.expander("📋 プロンプトを表示", expanded=True):
        st.code(prompt, language=None)
    st.write("")
    publish_prep = st.text_area(
        "Claudeの返答",
        value=st.session_state.publish_prep,
        height=320,
        placeholder="アイキャッチプロンプト・ハッシュタグ・マガジン提案...",
    )

    st.write("")
    st.markdown("### 🖼️ アイキャッチ画像をアップロード")
    st.caption("Gemini Nano Banana等で生成した画像を保存できます。後からKPI画面でも見返せます。")

    uploaded = st.file_uploader(
        "画像ファイル（PNG / JPG）",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        # ファイル名はタイトルから生成
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y%m%d_%H%M")
        safe_title = "".join(c for c in (st.session_state.article_title or "untitled") if c.isalnum() or c in "あ-んア-ン一-龯ぁ-ゔー_- ")[:40].strip() or "untitled"
        ext = uploaded.name.split(".")[-1]
        save_path = EYECATCH_DIR / f"{ts}_{safe_title}.{ext}"
        save_path.write_bytes(uploaded.getvalue())
        st.session_state.eyecatch_path = str(save_path)
        st.success(f"保存しました：{save_path.name}")
        st.image(str(save_path), use_container_width=True)
    elif st.session_state.eyecatch_path:
        st.info(f"既に保存済み：{Path(st.session_state.eyecatch_path).name}")
        if Path(st.session_state.eyecatch_path).exists():
            st.image(st.session_state.eyecatch_path, use_container_width=True)

    st.write("")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("← 戻る", use_container_width=True):
            go_to(5)
    with c2:
        if st.button("次へ → 最終レビュー", type="primary", disabled=not publish_prep.strip(), use_container_width=True):
            st.session_state.publish_prep = publish_prep
            go_to(7)

# ── STEP 7 ───────────────────────────────────────────────────────────────
elif step == 7:
    if st.session_state.saved_path:
        st.markdown(
            f'<div class="save-success">✅ <strong>保存完了！</strong><br><code>{st.session_state.saved_path}</code></div>',
            unsafe_allow_html=True,
        )
        if st.session_state.notion_result:
            (st.success if st.session_state.notion_result.startswith("Notion に") else st.warning)(st.session_state.notion_result)
        st.write("")
        st.markdown("**次のステップ：**")
        st.caption("1️⃣ Noteで記事を実際に公開 → 2️⃣ 公開後のURLを入力して SNS投稿文を生成")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 新しい記事を作成", use_container_width=True):
                reset()
        with c2:
            if st.button("▶️ SNS展開へ進む", type="primary", use_container_width=True):
                go_to(8)
    else:
        st.success("記事と公開準備の内容を確認して保存してください。")
        article_title = st.text_input("記事タイトル", value=st.session_state.article_title)

        tab_a, tab_p = st.tabs(["📄 記事本文", "🎨 公開準備"])
        with tab_a:
            full_article = f"{st.session_state.article_first}\n\n---\n\n{st.session_state.article_second}"
            article_edited = st.text_area("記事本文", value=full_article, height=480, label_visibility="collapsed")
        with tab_p:
            publish_prep_edited = st.text_area("公開準備", value=st.session_state.publish_prep, height=480, label_visibility="collapsed")

        st.divider()
        sync_notion = st.checkbox("Notionデータベースにも追加する", value=True)
        st.caption("Note URL未入力のためステータスは「アイデア」。SNS展開でURLを入れると「投稿済み」に更新。")

        st.write("")
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("← 戻る", use_container_width=True):
                go_to(6)
        with c2:
            if st.button("💾 保存して完了", type="primary", disabled=not article_title.strip(), use_container_width=True):
                st.session_state.article_title = article_title
                st.session_state.publish_prep = publish_prep_edited

                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                output_file = OUTPUTS_DIR / f"{timestamp}_note記事.md"
                content = f"""# {article_title}

**作成日時**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Note URL**: {st.session_state.note_url or "（未入力）"}

---

## 記事本文

{article_edited}

---

## 公開準備（アイキャッチ・タグ・マガジン）

{publish_prep_edited}

---

<details>
<summary>元データ（文字起こし・要約・構成案）</summary>

### 文字起こし
{st.session_state.transcription}

### 要約
{st.session_state.summary}

### 構成案
{st.session_state.outline}

</details>
"""
                output_file.write_text(content, encoding="utf-8")
                st.session_state.saved_path = str(output_file)

                if sync_notion:
                    ok, msg, page_id = sync_to_notion(
                        title=article_title,
                        url=st.session_state.note_url,
                        memo=st.session_state.summary,
                    )
                    st.session_state.notion_result = msg
                    st.session_state.notion_page_id = page_id
                else:
                    st.session_state.notion_result = ""
                st.rerun()

# ── STEP 8 ───────────────────────────────────────────────────────────────
elif step == 8:
    st.info("Noteで記事を公開した後、URLを入力してXとThreadsの投稿文を生成します。")
    note_url = st.text_input("公開後のNote URL", value=st.session_state.note_url, placeholder="https://note.com/pollyjack/n/...")

    if note_url and note_url != st.session_state.note_url:
        st.session_state.note_url = note_url
        if st.session_state.notion_page_id:
            ok, msg = update_notion_url(st.session_state.notion_page_id, note_url)
            (st.success if ok else st.warning)("Notionステータスを「投稿済み」に更新しました" if ok else msg)

    if not note_url:
        st.caption("👆 URLを入力すると、投稿文生成プロンプトが表示されます。")
    else:
        full_article = f"{st.session_state.article_first}\n\n{st.session_state.article_second}"
        tab_x, tab_t = st.tabs(["🐦 X（スレッド型推奨）", "🧵 Threads"])

        with tab_x:
            with st.expander("📋 Xプロンプトを表示", expanded=True):
                st.code(load_prompt("06_x_post.md", article=full_article, url=note_url), language=None)
            st.write("")
            x_post = st.text_area("X投稿文", value=st.session_state.x_post, height=240, placeholder="親ツイート + 返信1 + 返信2...")
            if x_post != st.session_state.x_post:
                st.session_state.x_post = x_post

        with tab_t:
            with st.expander("📋 Threadsプロンプトを表示", expanded=True):
                st.code(load_prompt("08_threads_post.md", title=st.session_state.article_title or "", article=full_article, url=note_url), language=None)
            st.write("")
            threads_post = st.text_area("Threads投稿文", value=st.session_state.threads_post, height=240)
            if threads_post != st.session_state.threads_post:
                st.session_state.threads_post = threads_post

        st.divider()
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("← 保存画面に戻る", use_container_width=True):
                go_to(7)
        with c2:
            if st.button("🔄 新しい記事を作成", type="primary", use_container_width=True):
                reset()
