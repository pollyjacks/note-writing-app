"""過去記事リバイバル：記事ローダーと時期性スコアリング"""
from datetime import date, datetime
from pathlib import Path
import re

ARCHIVE_DIR = Path(__file__).parent.parent.parent / "Note" / "02_コンテンツ" / "投稿文アーカイブ"
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"

# 月ごとの季節キーワード
SEASONAL_KEYWORDS: dict[int, list[str]] = {
    1: ["正月", "新年", "目標", "リセット", "1月", "抱負"],
    2: ["冬", "停滞", "バレンタイン", "2月", "寒"],
    3: ["卒業", "別れ", "年度末", "3月", "春", "区切り"],
    4: ["新生活", "新年度", "4月", "新人", "環境変化", "始まり", "春", "焦燥"],
    5: ["GW", "連休", "五月病", "疲れ", "5月", "無気力"],
    6: ["梅雨", "だるい", "気分", "6月", "停滞"],
    7: ["夏", "暑", "疲弊", "7月", "眠れない"],
    8: ["お盆", "帰省", "夏", "8月", "家族"],
    9: ["秋", "内省", "センチメンタル", "9月", "感傷"],
    10: ["秋", "読書", "思考", "10月", "内面"],
    11: ["冬", "孤独", "寒", "11月", "もの悲しい"],
    12: ["年末", "振り返り", "忘年", "12月", "総括"],
}

# 曜日ごとのキーワード（0=月, 6=日）
WEEKDAY_KEYWORDS: dict[int, list[str]] = {
    0: ["月曜", "憂鬱", "ブルー", "仕事行きたくない"],
    1: ["火曜"],
    2: ["水曜", "中だるみ"],
    3: ["木曜"],
    4: ["金曜", "週末", "解放"],
    5: ["土曜", "休日"],
    6: ["日曜", "サザエさん", "明日", "月曜憂鬱", "休日の夕方"],
}

MIN_DAYS_FOR_REUSE = 14   # これ未満は新しすぎて再投稿NG
BONUS_DAYS = 60           # これ以上経過していればボーナス


def _parse_archive_file(path: Path) -> dict | None:
    """Note/02_コンテンツ/投稿文アーカイブ/ のMDをパース"""
    m = re.match(r"No\.(\d+)_(.+)\.md$", path.name)
    if not m:
        return None
    body = path.read_text(encoding="utf-8")
    return {
        "source": "archive",
        "no": int(m.group(1)),
        "title": m.group(2).strip(),
        "body": body,
        "date": "",
        "url": "",
        "path": str(path),
    }


def _parse_output_file(path: Path) -> dict | None:
    """app/outputs/*.md（執筆フロー保存物）をパース"""
    body = path.read_text(encoding="utf-8")
    title_m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else path.stem
    date_m = re.search(r"\*\*作成日時\*\*:\s*(\d{4}-\d{2}-\d{2})", body)
    date_str = date_m.group(1) if date_m else ""
    url_m = re.search(r"\*\*Note URL\*\*:\s*(https?://\S+)", body)
    url = url_m.group(1) if url_m else ""
    return {
        "source": "output",
        "no": None,
        "title": title,
        "body": body,
        "date": date_str,
        "url": url,
        "path": str(path),
    }


def load_all_posts() -> list[dict]:
    """アーカイブ + outputs の過去記事をすべて読み込み"""
    posts: list[dict] = []
    if ARCHIVE_DIR.exists():
        for f in ARCHIVE_DIR.glob("*.md"):
            p = _parse_archive_file(f)
            if p:
                posts.append(p)
    if OUTPUTS_DIR.exists():
        for f in OUTPUTS_DIR.glob("*.md"):
            p = _parse_output_file(f)
            if p:
                posts.append(p)
    return posts


def enrich_with_notion(posts: list[dict]) -> list[dict]:
    """Notion の投稿済み情報で日付・URLを補完（タイトル部分一致）"""
    try:
        from lib.notion import fetch_published
        pub, _ = fetch_published()
    except Exception:
        return posts

    for p in posts:
        if p["date"] and p["url"]:
            continue
        for np in pub:
            nt = np.get("title", "")
            if nt and (nt in p["title"] or p["title"] in nt):
                if not p["date"]:
                    p["date"] = np.get("date", "")
                if not p["url"]:
                    p["url"] = np.get("url", "")
                break
    return posts


def score_post(post: dict, today: date) -> tuple[int, list[str]]:
    """時期性スコアと判定理由を返す"""
    score = 0
    reasons: list[str] = []
    haystack = post["title"] + "\n" + post["body"][:1500]

    # 季節キーワード
    month_kw = SEASONAL_KEYWORDS.get(today.month, [])
    matched = [k for k in month_kw if k in haystack]
    if matched:
        score += len(matched) * 2
        reasons.append(f"{today.month}月キーワード: {', '.join(matched[:3])}")

    # 曜日キーワード
    wd_kw = WEEKDAY_KEYWORDS.get(today.weekday(), [])
    matched_wd = [k for k in wd_kw if k in haystack]
    if matched_wd:
        score += len(matched_wd)
        reasons.append(f"曜日マッチ: {', '.join(matched_wd[:2])}")

    # 経過日数
    if post["date"]:
        try:
            posted = datetime.strptime(post["date"][:10], "%Y-%m-%d").date()
            days_ago = (today - posted).days
            if days_ago < MIN_DAYS_FOR_REUSE:
                score -= 10
                reasons.append(f"投稿{days_ago}日前（新しすぎ）")
            elif days_ago >= BONUS_DAYS:
                score += 2
                reasons.append(f"経過{days_ago}日（再利用好機）")
            else:
                reasons.append(f"経過{days_ago}日")
        except ValueError:
            pass
    else:
        reasons.append("投稿日不明")

    return score, reasons


def suggest_today(top_n: int = 3) -> tuple[list[dict], str]:
    """今日のリバイバル候補を返す。各dictに score, reasons を追加"""
    posts = load_all_posts()
    if not posts:
        return [], "過去記事が見つかりません"
    posts = enrich_with_notion(posts)
    today = date.today()
    scored = []
    for p in posts:
        s, r = score_post(p, today)
        p2 = {**p, "score": s, "reasons": r}
        scored.append(p2)
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = [x for x in scored if x["score"] > 0][:top_n]
    return top, ""
