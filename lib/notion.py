"""Notion API ラッパー（共通モジュール）"""
from datetime import datetime
import os
import streamlit as st


def _secret(key: str) -> str:
    """Streamlit Cloud の st.secrets → .env の順で取得"""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, "")


def get_notion_client():
    token = _secret("NOTION_TOKEN")
    if not token or token.startswith("secret_ここに"):
        return None, "NOTION_TOKEN が未設定です"
    try:
        from notion_client import Client
        return Client(auth=token), None
    except Exception as e:
        return None, f"Notion クライアント初期化エラー: {e}"


def get_db_id() -> str:
    return _secret("NOTION_DB_ID")


@st.cache_data(ttl=3600)
def get_data_source_id() -> str:
    """database_id から data_source_id を取得（クエリ用）"""
    notion, err = get_notion_client()
    if err:
        return ""
    db_id = get_db_id()
    if not db_id:
        return ""
    try:
        db = notion.databases.retrieve(database_id=db_id)
        data_sources = db.get("data_sources", [])
        if data_sources and isinstance(data_sources, list):
            return data_sources[0].get("id", "")
    except Exception:
        pass
    return ""


def sync_to_notion(title: str, url: str, memo: str) -> tuple[bool, str, str]:
    """新規ページをNotionに作成。返り値: (成功, メッセージ, page_id)"""
    notion, err = get_notion_client()
    if err:
        return False, err, ""
    db_id = get_db_id()
    if not db_id:
        return False, "NOTION_DB_ID が未設定です", ""

    try:
        status = "投稿済み" if url else "アイデア"
        props: dict = {
            "タイトル": {"title": [{"text": {"content": title}}]},
            "ステータス": {"select": {"name": status}},
            "タイプ": {"select": {"name": "無料"}},
        }
        if url:
            props["URL"] = {"url": url}
        if memo:
            props["メモ"] = {"rich_text": [{"text": {"content": memo[:2000]}}]}
        props["投稿日時"] = {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}

        result = notion.pages.create(parent={"database_id": db_id}, properties=props)
        return True, f"Notion に「{title}」を追加（ステータス: {status}）", result.get("id", "")
    except Exception as e:
        return False, f"Notion 同期エラー: {e}", ""


def update_notion_url(page_id: str, url: str) -> tuple[bool, str]:
    """既存ページにURLとステータスを更新"""
    notion, err = get_notion_client()
    if err or not page_id:
        return False, err or "ページIDがありません"
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "URL": {"url": url},
                "ステータス": {"select": {"name": "投稿済み"}},
            },
        )
        return True, "Notion更新しました"
    except Exception as e:
        return False, f"Notion更新エラー: {e}"


def fetch_ideas() -> tuple[list, str]:
    """ステータスが「アイデア」のページ一覧を取得"""
    notion, err = get_notion_client()
    if err:
        return [], err
    db_id = get_db_id()
    if not db_id:
        return [], "NOTION_DB_ID が未設定です"

    try:
        # notion_client v3 は data_sources.query を使う
        result = notion.data_sources.query(
            data_source_id=get_data_source_id(),
            filter={"property": "ステータス", "select": {"equals": "アイデア"}},
            page_size=100,
        )
        ideas = []
        for page in result.get("results", []):
            props = page.get("properties", {})
            title_prop = props.get("タイトル", {}).get("title", [])
            title = title_prop[0].get("plain_text", "") if title_prop else "(no title)"
            memo_prop = props.get("メモ", {}).get("rich_text", [])
            memo = memo_prop[0].get("plain_text", "") if memo_prop else ""
            ideas.append({
                "id": page["id"],
                "title": title,
                "memo": memo,
                "url": page.get("url", ""),
            })
        return ideas, ""
    except Exception as e:
        return [], f"アイデア取得エラー: {e}"


def fetch_published() -> tuple[list, str]:
    """ステータスが「投稿済み」のページ一覧を取得（KPI集計用）"""
    notion, err = get_notion_client()
    if err:
        return [], err
    try:
        result = notion.data_sources.query(
            data_source_id=get_data_source_id(),
            filter={"property": "ステータス", "select": {"equals": "投稿済み"}},
            page_size=100,
        )
        published = []
        for page in result.get("results", []):
            props = page.get("properties", {})
            title_prop = props.get("タイトル", {}).get("title", [])
            title = title_prop[0].get("plain_text", "") if title_prop else "(no title)"
            url_prop = props.get("URL", {}).get("url", "")
            date_prop = props.get("投稿日時", {}).get("date", {})
            date_str = date_prop.get("start", "") if date_prop else ""
            published.append({
                "id": page["id"],
                "title": title,
                "url": url_prop,
                "date": date_str,
            })
        return published, ""
    except Exception as e:
        return [], f"投稿済み取得エラー: {e}"


def add_idea(title: str, memo: str = "", reference_url: str = "") -> tuple[bool, str]:
    """新しいアイデアをNotionに追加"""
    notion, err = get_notion_client()
    if err:
        return False, err
    db_id = get_db_id()
    if not db_id:
        return False, "NOTION_DB_ID が未設定です"

    try:
        props: dict = {
            "タイトル": {"title": [{"text": {"content": title}}]},
            "ステータス": {"select": {"name": "アイデア"}},
            "タイプ": {"select": {"name": "無料"}},
        }
        if memo:
            full_memo = memo
            if reference_url:
                full_memo += f"\n参考: {reference_url}"
            props["メモ"] = {"rich_text": [{"text": {"content": full_memo[:2000]}}]}
        notion.pages.create(parent={"database_id": db_id}, properties=props)
        return True, f"「{title}」をアイデアとして追加しました"
    except Exception as e:
        return False, f"アイデア追加エラー: {e}"
