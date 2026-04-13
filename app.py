import os
import streamlit as st
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

def _secret(key: str) -> str:
    """Streamlit Cloud の st.secrets → .env の順で取得"""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, "")

# ── Notion同期 ────────────────────────────────────────────────────────────
def sync_to_notion(title: str, url: str, memo: str) -> tuple[bool, str, str]:
    token = _secret("NOTION_TOKEN")
    db_id = _secret("NOTION_DB_ID")
    if not token or token.startswith("secret_ここに"):
        return False, "NOTION_TOKEN が未設定です（app/.env を確認してください）", ""
    if not db_id:
        return False, "NOTION_DB_ID が未設定です", ""

    try:
        from notion_client import Client
        notion = Client(auth=token)

        status = "投稿済み" if url else "アイデア"
        props: dict = {
            "タイトル": {"title": [{"text": {"content": title}}]},
            "ステータス": {"select": {"name": status}},
            "タイプ":    {"select": {"name": "無料"}},
        }
        if url:
            props["URL"] = {"url": url}
        if memo:
            props["メモ"] = {"rich_text": [{"text": {"content": memo[:2000]}}]}
        today = datetime.now().strftime("%Y-%m-%d")
        props["投稿日時"] = {"date": {"start": today}}

        result = notion.pages.create(parent={"database_id": db_id}, properties=props)
        page_id = result.get("id", "")
        return True, f"Notion に「{title}」を追加しました（ステータス: {status}）", page_id
    except Exception as e:
        return False, f"Notion 同期エラー: {e}", ""

def update_notion_url(page_id: str, url: str) -> tuple[bool, str]:
    """既存のNotionページにURLとステータスを更新"""
    token = _secret("NOTION_TOKEN")
    if not token or not page_id:
        return False, "トークンまたはページIDがありません"
    try:
        from notion_client import Client
        notion = Client(auth=token)
        notion.pages.update(
            page_id=page_id,
            properties={
                "URL": {"url": url},
                "ステータス": {"select": {"name": "投稿済み"}},
            }
        )
        return True, "Notion更新しました"
    except Exception as e:
        return False, f"Notion更新エラー: {e}"

# ── 初期設定 ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Note執筆アシスタント",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── カスタムCSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    .step-label {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 0.2rem;
    }
    .review-badge {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 6px;
        padding: 8px 14px;
        font-size: 0.9rem;
        color: #92400e;
        margin-bottom: 1rem;
        display: inline-block;
    }
    .copy-hint {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        padding: 8px 14px;
        font-size: 0.88rem;
        color: #1e40af;
        border-radius: 0 6px 6px 0;
        margin-bottom: 1rem;
    }
    .save-success {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 16px;
        color: #166534;
    }
</style>
""", unsafe_allow_html=True)

# ── セッションステート初期化 ──────────────────────────────────────────────
DEFAULTS = {
    "step": 0,
    "transcription": "",
    "summary": "",
    "outline": "",
    "article_first": "",
    "article_second": "",
    "publish_prep": "",
    "x_post": "",
    "threads_post": "",
    "note_url": "",
    "article_title": "",
    "saved_path": "",
    "notion_result": "",
    "notion_page_id": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── ヘルパー ──────────────────────────────────────────────────────────────
def load_prompt(filename: str, **kwargs) -> str:
    text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    for key, value in kwargs.items():
        text = text.replace(f"{{{key}}}", value)
    return text

def parse_titles(outline_text: str) -> list[str]:
    """構成案テキストから3つのタイトル候補を抽出"""
    import re
    titles = []
    # 【タイトル案】以降から1. 2. 3. でマッチ
    m = re.search(r"【タイトル案】.*?(?=【|##|\Z)", outline_text, re.DOTALL)
    target = m.group(0) if m else outline_text[:1500]
    # 1. 2. 3. 形式で抽出
    for match in re.finditer(r"^\s*[1-3][.、)]\s*(.+?)$", target, re.MULTILINE):
        title = match.group(1).strip()
        # 括弧注釈を除去
        title = re.sub(r"（[^）]*重視[^）]*）", "", title).strip()
        title = re.sub(r"\([^)]*重視[^)]*\)", "", title).strip()
        if title and len(title) > 5:
            titles.append(title)
    return titles[:3]

def go_to(step: int):
    st.session_state.step = step
    st.rerun()

def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()

STEPS = [
    "文字起こし入力",          # 0
    "① 要約プロンプト",         # 1
    "② 構成案プロンプト",       # 2
    "★ 構成案レビュー・タイトル選択",  # 3
    "③ 執筆（前半）",           # 4
    "④ 執筆（後半）",           # 5
    "⑤ 公開準備",              # 6
    "★ 最終レビュー・保存",      # 7
    "⑥ SNS展開（公開後）",     # 8
]

REVIEW_STEPS = {3, 7}

# ── ヘッダー ──────────────────────────────────────────────────────────────
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.title("📝 Note執筆アシスタント")
with col_reset:
    st.write("")
    if st.button("🔄 最初からやり直す", help="入力内容をすべてリセットします"):
        reset()

# ステップ表示
step = st.session_state.step
is_review = step in REVIEW_STEPS

st.markdown(f'<div class="step-label">Step {step + 1} / {len(STEPS)}</div>', unsafe_allow_html=True)
if is_review:
    st.markdown(f'<div class="review-badge">⭐ {STEPS[step]} — あなたの確認が必要です</div>', unsafe_allow_html=True)
else:
    st.subheader(STEPS[step])

st.progress(step / (len(STEPS) - 1))
st.divider()

# ── STEP 0: 文字起こし入力 ────────────────────────────────────────────────
if step == 0:
    st.info("iPhoneで文字起こしたテキストをそのまま貼り付けてください。")

    transcription = st.text_area(
        "文字起こしテキスト",
        value=st.session_state.transcription,
        height=420,
        placeholder="ここに文字起こしのテキストを貼り付けてください...",
        label_visibility="collapsed",
    )

    char_count = len(transcription.strip())
    st.caption(f"文字数: {char_count:,} 文字")

    st.write("")
    if st.button(
        "次へ → 要約プロンプトを生成",
        type="primary",
        disabled=not transcription.strip(),
        use_container_width=True,
    ):
        st.session_state.transcription = transcription
        go_to(1)

# ── STEP 1: 要約プロンプト ────────────────────────────────────────────────
elif step == 1:
    st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付け、返答をここに貼り戻してください。</div>', unsafe_allow_html=True)

    prompt = load_prompt("01_summarize.md", transcription=st.session_state.transcription)
    with st.expander("📋 プロンプトを表示（クリックで開く）", expanded=True):
        st.code(prompt, language=None)

    st.write("")
    summary = st.text_area(
        "Claudeの返答をここに貼り付けてください",
        value=st.session_state.summary,
        height=300,
        placeholder="Claude.aiの応答（要約・法則化・INFJペイン）をここに貼り付け...",
    )

    st.write("")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 戻る", use_container_width=True):
            go_to(0)
    with col2:
        if st.button(
            "次へ → 構成案プロンプトを生成",
            type="primary",
            disabled=not summary.strip(),
            use_container_width=True,
        ):
            st.session_state.summary = summary
            go_to(2)

# ── STEP 2: 構成案プロンプト ──────────────────────────────────────────────
elif step == 2:
    st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付け、返答をここに貼り戻してください。</div>', unsafe_allow_html=True)

    prompt = load_prompt(
        "02_outline.md",
        transcription=st.session_state.transcription,
        summary=st.session_state.summary,
    )
    with st.expander("📋 プロンプトを表示（クリックで開く）", expanded=True):
        st.code(prompt, language=None)

    st.write("")
    outline = st.text_area(
        "Claudeの返答をここに貼り付けてください",
        value=st.session_state.outline,
        height=300,
        placeholder="Claude.aiの応答（タイトル案・構成案）をここに貼り付け...",
    )

    st.write("")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 戻る", use_container_width=True):
            go_to(1)
    with col2:
        if st.button(
            "次へ → 構成案をレビュー",
            type="primary",
            disabled=not outline.strip(),
            use_container_width=True,
        ):
            st.session_state.outline = outline
            go_to(3)

# ── STEP 3: ★ 構成案レビュー・タイトル選択 ───────────────────────────────
elif step == 3:
    st.success("構成案を確認・修正し、タイトルを選択してから執筆を開始してください。")

    outline = st.text_area(
        "構成案（直接編集できます）",
        value=st.session_state.outline,
        height=420,
    )

    st.write("")
    st.markdown("### 📌 タイトル選択")

    # 構成案からタイトル候補を抽出
    parsed_titles = parse_titles(outline)

    if parsed_titles:
        st.caption(f"構成案から {len(parsed_titles)} 個のタイトル候補を検出しました。選んでください（または下のカスタム入力）。")
        options = parsed_titles + ["✏️ 自分で入力する"]
        default_idx = 0
        if st.session_state.article_title in parsed_titles:
            default_idx = parsed_titles.index(st.session_state.article_title)
        choice = st.radio(
            "候補から選択",
            options,
            index=default_idx,
            label_visibility="collapsed",
        )
        if choice == "✏️ 自分で入力する":
            custom_title = st.text_input(
                "カスタムタイトル",
                value=st.session_state.article_title if st.session_state.article_title not in parsed_titles else "",
                placeholder="タイトルを入力してください",
            )
            selected_title = custom_title
        else:
            selected_title = choice
    else:
        st.caption("構成案からタイトル候補を自動検出できませんでした。タイトルを入力してください。")
        selected_title = st.text_input(
            "タイトル",
            value=st.session_state.article_title,
            placeholder="タイトルを入力してください",
        )

    st.write("")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 戻って修正", use_container_width=True):
            st.session_state.outline = outline
            st.session_state.article_title = selected_title
            go_to(2)
    with col2:
        if st.button(
            "✅ この構成案で執筆を開始する",
            type="primary",
            disabled=not (selected_title or "").strip(),
            use_container_width=True,
        ):
            st.session_state.outline = outline
            st.session_state.article_title = selected_title
            go_to(4)

# ── STEP 4: 執筆（前半） ──────────────────────────────────────────────────
elif step == 4:
    st.markdown('<div class="copy-hint">👇 以下の2つのプロンプトを<strong>順番に</strong> Claude.ai に送ってください。<br>1つ目で内容を読み込ませ、2つ目で前半を執筆します。</div>', unsafe_allow_html=True)

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
        prompt_first = load_prompt("04_write_first_half.md")
        st.code(prompt_first, language=None)

    st.write("")
    article_first = st.text_area(
        "前半の執筆結果をここに貼り付けてください",
        value=st.session_state.article_first,
        height=350,
        placeholder="Claude.aiが執筆した記事の前半をここに貼り付け...",
    )

    st.write("")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 戻る", use_container_width=True):
            go_to(3)
    with col2:
        if st.button(
            "次へ → 後半を執筆",
            type="primary",
            disabled=not article_first.strip(),
            use_container_width=True,
        ):
            st.session_state.article_first = article_first
            go_to(5)

# ── STEP 5: 執筆（後半） ──────────────────────────────────────────────────
elif step == 5:
    st.markdown('<div class="copy-hint">👇 前半を書いたClaude.aiの会話を<strong>続けて</strong>、以下のプロンプトを送ってください。</div>', unsafe_allow_html=True)

    prompt_second = load_prompt("05_write_second_half.md")
    with st.expander("📋 プロンプトを表示（クリックで開く）", expanded=True):
        st.code(prompt_second, language=None)

    st.write("")
    article_second = st.text_area(
        "後半の執筆結果をここに貼り付けてください",
        value=st.session_state.article_second,
        height=350,
        placeholder="Claude.aiが執筆した記事の後半をここに貼り付け...",
    )

    st.write("")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 戻る", use_container_width=True):
            go_to(4)
    with col2:
        if st.button(
            "次へ → 公開準備",
            type="primary",
            disabled=not article_second.strip(),
            use_container_width=True,
        ):
            st.session_state.article_second = article_second
            go_to(6)

# ── STEP 6: 公開準備（アイキャッチ・ハッシュタグ・マガジン） ─────────────
elif step == 6:
    st.info("Note公開用のアイキャッチプロンプト・ハッシュタグ・マガジン提案を生成します。")

    full_article = f"{st.session_state.article_first}\n\n{st.session_state.article_second}"
    prompt = load_prompt(
        "07_publish_prep.md",
        title=st.session_state.article_title or "（タイトル未入力）",
        article=full_article,
    )

    st.markdown('<div class="copy-hint">👇 以下のプロンプトをコピーして <strong>Claude.ai</strong> に貼り付け、返答をここに貼り戻してください。</div>', unsafe_allow_html=True)
    with st.expander("📋 プロンプトを表示（クリックで開く）", expanded=True):
        st.code(prompt, language=None)

    st.write("")
    publish_prep = st.text_area(
        "Claudeの返答をここに貼り付けてください",
        value=st.session_state.publish_prep,
        height=320,
        placeholder="アイキャッチプロンプト・ハッシュタグ・マガジン提案の全体をここに貼り付け...",
    )

    st.write("")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← 戻る", use_container_width=True):
            go_to(5)
    with col2:
        if st.button(
            "次へ → 最終レビュー",
            type="primary",
            disabled=not publish_prep.strip(),
            use_container_width=True,
        ):
            st.session_state.publish_prep = publish_prep
            go_to(7)

# ── STEP 7: ★ 最終レビュー・保存 ─────────────────────────────────────────
elif step == 7:
    if st.session_state.saved_path:
        st.markdown(f"""
        <div class="save-success">
            ✅ <strong>保存完了！</strong><br>
            <code>{st.session_state.saved_path}</code>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.notion_result:
            is_ok = st.session_state.notion_result.startswith("Notion に")
            if is_ok:
                st.success(st.session_state.notion_result)
            else:
                st.warning(st.session_state.notion_result)
        st.write("")
        st.markdown("**次のステップ：**")
        st.caption("1️⃣ Noteで記事を実際に公開 → 2️⃣ 公開後のURLを入力して SNS投稿文を生成")
        col_next1, col_next2 = st.columns(2)
        with col_next1:
            if st.button("🔄 新しい記事を作成", use_container_width=True):
                reset()
        with col_next2:
            if st.button("▶️ SNS展開へ進む", type="primary", use_container_width=True):
                go_to(8)
    else:
        st.success("記事と公開準備の内容を確認して保存してください。")

        # タイトル（Step 3で選択済み・ここで変更も可）
        article_title = st.text_input(
            "記事タイトル",
            value=st.session_state.article_title,
            placeholder="例：INFJが職場で消耗しないための4つのデトックス術",
        )

        tab_article, tab_prep = st.tabs(["📄 記事本文", "🎨 公開準備（アイキャッチ・タグ・マガジン）"])

        with tab_article:
            full_article = (
                st.session_state.article_first
                + "\n\n---\n\n"
                + st.session_state.article_second
            )
            article_edited = st.text_area(
                "記事本文",
                value=full_article,
                height=480,
                label_visibility="collapsed",
            )

        with tab_prep:
            publish_prep_edited = st.text_area(
                "公開準備",
                value=st.session_state.publish_prep,
                height=480,
                label_visibility="collapsed",
            )

        # Notion同期オプション
        st.divider()
        sync_notion = st.checkbox("Notionデータベースにも追加する", value=True)
        st.caption("この時点ではNote URL未入力のためステータスは「アイデア」。SNS展開ステップでURLを入力すると「投稿済み」に更新されます。")

        st.write("")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← 戻る", use_container_width=True):
                go_to(6)
        with col2:
            if st.button(
                "💾 保存して完了",
                type="primary",
                disabled=not article_title.strip(),
                use_container_width=True,
            ):
                st.session_state.article_title = article_title
                st.session_state.publish_prep = publish_prep_edited

                # ローカル保存
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

                # Notion同期（ページIDを保存）
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

# ── STEP 8: SNS展開（公開後） ────────────────────────────────────────────
elif step == 8:
    st.info("Noteで記事を公開した後、URLを入力してXとThreadsの投稿文を生成します。")

    note_url = st.text_input(
        "公開後のNote URL",
        value=st.session_state.note_url,
        placeholder="https://note.com/pollyjack/n/...",
    )

    if note_url and note_url != st.session_state.note_url:
        st.session_state.note_url = note_url
        # Notionのステータスも更新
        if st.session_state.notion_page_id:
            ok, msg = update_notion_url(st.session_state.notion_page_id, note_url)
            if ok:
                st.success(f"Notionのステータスを「投稿済み」に更新しました")
            else:
                st.warning(msg)

    if not note_url:
        st.caption("👆 URLを入力すると、投稿文生成プロンプトが表示されます。")
    else:
        full_article = f"{st.session_state.article_first}\n\n{st.session_state.article_second}"

        tab_x, tab_threads = st.tabs(["🐦 X（140字）", "🧵 Threads（500字）"])

        with tab_x:
            prompt_x = load_prompt(
                "06_x_post.md",
                article=full_article,
                url=note_url,
            )
            with st.expander("📋 Xプロンプトを表示", expanded=True):
                st.code(prompt_x, language=None)

            st.write("")
            x_post = st.text_area(
                "X投稿文",
                value=st.session_state.x_post,
                height=200,
                placeholder="Claude.aiが作成したX投稿文をここに貼り付け...",
            )
            if x_post != st.session_state.x_post:
                st.session_state.x_post = x_post

        with tab_threads:
            prompt_th = load_prompt(
                "08_threads_post.md",
                title=st.session_state.article_title or "",
                article=full_article,
                url=note_url,
            )
            with st.expander("📋 Threadsプロンプトを表示", expanded=True):
                st.code(prompt_th, language=None)

            st.write("")
            threads_post = st.text_area(
                "Threads投稿文",
                value=st.session_state.threads_post,
                height=240,
                placeholder="Claude.aiが作成したThreads投稿文をここに貼り付け...",
            )
            if threads_post != st.session_state.threads_post:
                st.session_state.threads_post = threads_post

        st.divider()
        st.write("")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("← 保存画面に戻る", use_container_width=True):
                go_to(7)
        with col2:
            if st.button("🔄 新しい記事を作成", type="primary", use_container_width=True):
                reset()
