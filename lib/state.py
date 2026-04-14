"""セッションステート管理（共通）"""
from pathlib import Path
import streamlit as st

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"
EYECATCH_DIR = Path(__file__).parent.parent / "eyecatches"
OUTPUTS_DIR.mkdir(exist_ok=True)
EYECATCH_DIR.mkdir(exist_ok=True)

WRITE_DEFAULTS = {
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
    "eyecatch_path": "",
}


def init_write_state():
    for k, v in WRITE_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_write_state():
    for k, v in WRITE_DEFAULTS.items():
        st.session_state[k] = v


def load_prompt(filename: str, **kwargs) -> str:
    text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    for key, value in kwargs.items():
        text = text.replace(f"{{{key}}}", value)
    return text


def parse_titles(outline_text: str) -> list[str]:
    """構成案テキストから3つのタイトル候補を抽出"""
    import re
    titles = []
    m = re.search(r"【タイトル案】.*?(?=【|##|\Z)", outline_text, re.DOTALL)
    target = m.group(0) if m else outline_text[:1500]
    for match in re.finditer(r"^\s*[1-3][.、)]\s*(.+?)$", target, re.MULTILINE):
        title = match.group(1).strip()
        title = re.sub(r"（[^）]*重視[^）]*）", "", title).strip()
        title = re.sub(r"\([^)]*重視[^)]*\)", "", title).strip()
        if title and len(title) > 5:
            titles.append(title)
    return titles[:3]
