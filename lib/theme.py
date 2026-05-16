"""アプリ共通のテーマ設定（ミニマル系）"""
import streamlit as st


def apply_minimal_theme():
    """ミニマル系テーマのCSSを適用"""
    st.markdown("""
<style>
    /* ── カラーパレット（ミニマル・モノトーン + アクセント） */
    :root {
        --bg: #fafafa;
        --surface: #ffffff;
        --border: #e5e5e5;
        --text: #1a1a1a;
        --text-muted: #737373;
        --accent: #2563eb;
        --accent-soft: #eff6ff;
        --success: #16a34a;
        --warning: #d97706;
    }

    /* ── 全体の余白とフォント */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 880px;
    }

    /* ── タイトル */
    h1 {
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text);
        margin-bottom: 0.5rem;
    }
    h2, h3 {
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--text);
    }

    /* ── ボタン */
    .stButton button {
        border-radius: 8px;
        border: 1px solid var(--border);
        font-weight: 500;
        transition: all 0.15s ease;
    }
    .stButton button:hover {
        border-color: var(--text);
    }
    .stButton button[kind="primary"] {
        background: var(--text);
        border-color: var(--text);
        color: white;
    }
    .stButton button[kind="primary"]:hover {
        background: #000;
        border-color: #000;
    }

    /* ── テキストエリア・インプット */
    .stTextArea textarea, .stTextInput input {
        border-radius: 8px;
        border-color: var(--border);
        font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    }

    /* ── サイドバー */
    section[data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }
    /* サイドバー内のすべてのテキストを濃い色に強制 */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] *,
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] div {
        color: var(--text) !important;
    }
    /* ナビゲーションのアクティブ項目 */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
        font-weight: 500;
        color: var(--text) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background: var(--accent-soft);
    }
    /* ページタイトル */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--text) !important;
    }

    /* ── カスタムバッジ */
    .step-label {
        font-size: 0.78rem;
        color: var(--text-muted);
        margin-bottom: 0.3rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .review-badge {
        background: #fef9c3;
        border: 1px solid #facc15;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 0.85rem;
        color: #854d0e;
        margin-bottom: 1rem;
        display: inline-block;
        font-weight: 500;
    }
    .copy-hint {
        background: var(--accent-soft);
        border-left: 3px solid var(--accent);
        padding: 10px 14px;
        font-size: 0.85rem;
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

    /* ── カード（アイデア・ナレッジ用） */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 12px;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .card:hover {
        border-color: #c4c4c4;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .card-title {
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--text);
        margin-bottom: 4px;
    }
    .card-meta {
        font-size: 0.78rem;
        color: var(--text-muted);
    }

    /* ── リマインダーカード */
    .reminder-card {
        border-radius: 8px;
        padding: 11px 14px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.88rem;
        border: 1px solid transparent;
        line-height: 1.45;
    }
    .reminder-card .r-icon { font-size: 1.05rem; flex-shrink: 0; }
    .reminder-card .r-text { color: var(--text); }
    .reminder-card .r-text strong { font-weight: 600; }
    .reminder-warn {
        background: #fffbeb;
        border-color: #fde68a;
    }
    .reminder-ok {
        background: #f0fdf4;
        border-color: #bbf7d0;
    }
    .reminder-info {
        background: var(--accent-soft);
        border-color: #bfdbfe;
    }
    .reminder-celebrate {
        background: #faf5ff;
        border-color: #e9d5ff;
    }
    .reminder-neutral {
        background: #f9fafb;
        border-color: var(--border);
    }

    /* ── メトリクス */
    [data-testid="stMetricValue"] {
        font-size: 1.9rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em;
        color: var(--text) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 500;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--text-muted) !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.78rem !important;
    }

    /* ── サイドバー セクション見出し */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"],
    section[data-testid="stSidebar"] .st-emotion-cache-title {
        font-size: 0.68rem !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        margin-top: 1rem !important;
    }

    /* ── プログレスバー */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent) 0%, #60a5fa 100%);
        border-radius: 99px;
    }
    .stProgress > div > div {
        border-radius: 99px;
        background: #e5e7eb;
    }
</style>
    """, unsafe_allow_html=True)
