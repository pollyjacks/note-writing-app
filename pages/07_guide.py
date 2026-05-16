"""ガイド：このツールでできること・使い方"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme

apply_minimal_theme()

st.markdown("""
<style>
.section-card {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    height: 100%;
    background: var(--surface);
}
.section-card .section-title {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 10px;
}
.section-card .tool-item {
    font-size: 0.9rem;
    color: var(--text);
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: baseline;
    gap: 8px;
}
.section-card .tool-item:last-child { border-bottom: none; }
.section-card .tool-desc {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 1px;
}
.flow-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin: 8px 0;
}
.flow-node {
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.82rem;
    background: var(--surface);
    white-space: nowrap;
}
.flow-node.accent {
    border-color: var(--accent);
    background: var(--accent-soft);
    color: #1e40af;
    font-weight: 500;
}
.flow-node.muted {
    border-color: #d4d4d4;
    background: #f5f5f5;
    color: var(--text-muted);
    font-style: italic;
}
.flow-arrow {
    color: var(--text-muted);
    font-size: 1rem;
    flex-shrink: 0;
}
.flow-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 14px 0 4px;
}
</style>
""", unsafe_allow_html=True)

st.title("📖 ガイド")
st.caption("各機能の概要・フロー・使い方をまとめたマニュアルです。")

# ════════════════════════════════════════════
# セクションカード
# ════════════════════════════════════════════
st.markdown("## 🗂️ 機能マップ")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
<div class="section-card">
  <div class="section-title">📊 ダッシュボード</div>
  <div class="tool-item">🏠 ホーム<span class="tool-desc">今日のタスク・全体サマリー</span></div>
  <div class="tool-item">📊 KPI<span class="tool-desc">月間目標・投稿カレンダー</span></div>
  <div class="tool-item">📖 ガイド<span class="tool-desc">このページ</span></div>
</div>
""", unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="section-card">
  <div class="section-title">✍️ 執筆</div>
  <div class="tool-item">🎤 録音準備<span class="tool-desc">アジェンダ・問いかけ生成</span></div>
  <div class="tool-item">📝 執筆（無料）<span class="tool-desc">文字起こし→記事→SNS</span></div>
  <div class="tool-item">💴 有料記事<span class="tool-desc">読書メモ→深掘り→有料執筆</span></div>
  <div class="tool-item">🔁 リバイバル<span class="tool-desc">過去記事をXで切り取り再拡散</span></div>
</div>
""", unsafe_allow_html=True)

with col3:
    st.markdown("""
<div class="section-card">
  <div class="section-title">📥 情報・インプット</div>
  <div class="tool-item">💡 アイデア<span class="tool-desc">記事ネタのストック（Notion連携）</span></div>
  <div class="tool-item">📚 ナレッジ<span class="tool-desc">外部情報の蓄積・検索</span></div>
  <br>
  <div class="section-title" style="margin-top:4px">⚙️ その他</div>
  <div class="tool-item">⚙️ 設定<span class="tool-desc">プロンプトの閲覧・編集</span></div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════
# フロー図
# ════════════════════════════════════════════
st.markdown("## 🗺️ 記事制作フロー")

tab_free, tab_paid = st.tabs(["📝 無料記事フロー", "💴 有料記事フロー"])

with tab_free:
    st.markdown("""
<div class="flow-label">① 準備・ネタ出し</div>
<div class="flow-row">
  <div class="flow-node">💡 アイデアストック</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node accent">🎤 録音準備（任意）</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">📱 iPhoneで録音</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">🔤 文字起こし</div>
</div>

<div class="flow-label">② 執筆（Step 0〜8）</div>
<div class="flow-row">
  <div class="flow-node accent">📝 執筆ページへ</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">要約</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">構成案</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">前半執筆</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">後半執筆</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">公開準備・保存</div>
</div>

<div class="flow-label">③ 公開・拡散・記録</div>
<div class="flow-row">
  <div class="flow-node">Note 公開</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node accent">X・Threads 投稿文生成</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">📊 KPI 記録</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node accent">🔁 リバイバル（後日）</div>
</div>
""", unsafe_allow_html=True)

    st.caption("📥 ナレッジ・インプット分析は並行して随時蓄積。執筆のアイデア源として活用。")

with tab_paid:
    st.markdown("""
<div class="flow-label">① 読書・メモ</div>
<div class="flow-row">
  <div class="flow-node">📚 本を読む（付箋）</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">Notion に読書メモを書き溜め</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node accent">💴 有料記事ページ › Tab1 で貼り付け</div>
</div>

<div class="flow-label">② アジェンダ生成 → 録音</div>
<div class="flow-row">
  <div class="flow-node accent">📖 録音アジェンダ or 要約プロンプト生成</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">Claude.ai に貼り付け</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">🎙️ 独自視点を録音</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">🔤 文字起こし</div>
</div>

<div class="flow-label">③ 深掘りチェーン（Tab2）</div>
<div class="flow-row">
  <div class="flow-node">Step0 コンテキスト設定</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">Step1 構造化・KW抽出</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">Step2 パラダイムシフト</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">Step3 自分事化</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">Step4 持論言語化</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node accent">Step5 構成案 → 保存</div>
</div>

<div class="flow-label">④ 有料執筆（Tab3）</div>
<div class="flow-row">
  <div class="flow-node">構成案・文字起こしを読み込み</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node accent">前半執筆（無料エリア）</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node accent">後半執筆（有料エリア）</div>
  <span class="flow-arrow">→</span>
  <div class="flow-node">Note 有料公開</div>
</div>
""", unsafe_allow_html=True)

    st.caption("💡 深掘りチェーンの各ステップは Claude.ai との往復。Step5の構成案だけファイル保存されます。")

st.divider()

# ════════════════════════════════════════════
# 機能詳細（アコーディオン）
# ════════════════════════════════════════════
st.markdown("## 🔧 機能詳細")

with st.expander("🎤 録音準備 — テーマからアジェンダ・問いかけを生成"):
    st.markdown("""
**何ができるか**
- テーマを入れると、話すべきアジェンダ・深掘るための問い・盛り込むと良い視点を生成
- 録音中に見るカンペとして使える

**いつ使うか**
- 音声録音の**前**。テーマは決まっているが何を話すか整理したいとき
- すでに音声があり文字起こし済みの場合は **使わなくてOK**（執筆画面に直行）

**典型フロー**：テーマ入力 → プロンプトをClaude.aiにコピペ → 回答を貼り戻し → 録音
""")

with st.expander("📝 執筆（無料） — 文字起こしから記事完成・SNS展開まで（Step 0〜8）"):
    st.markdown("""
**何ができるか**
- iPhone文字起こしテキスト → 要約 → 構成案 → 前半執筆 → 後半執筆 → 公開準備 → SNS投稿文
- 各StepでClaude.aiにプロンプトを投げて回答を貼り戻す方式
- Notion「Note投稿用」DBに自動保存、URL入力で「投稿済み」ステータスに更新

| Step | 内容 |
|---|---|
| 0 | 文字起こし貼り付け |
| 1 | 要約プロンプト → 貼り戻し |
| 2 | 構成案プロンプト → 貼り戻し |
| 3 | 構成案レビュー・タイトル3案から選択 |
| 4 | 前半執筆 |
| 5 | 後半執筆 |
| 6 | 公開準備（アイキャッチ・ハッシュタグ・マガジン）|
| 7 | 最終レビュー → 保存 |
| 8 | Note公開後、URL入力 → X・Threads投稿文生成 |
""")

with st.expander("💴 有料記事 — 読書メモ → 深掘りチェーン → 有料執筆"):
    st.markdown("""
**何ができるか**
- Notionの読書メモから録音アジェンダ or 要約プロンプトを自動生成（Tab1）
- 5ステップの深掘りチェーンで「本をダシにした独自の持論」を引き出す（Tab2）
- 有料記事（無料エリア＋ペイウォール後）の執筆プロンプトを順番に表示（Tab3）

**いつ使うか**
- 読んだ本を元に有料記事を書くとき（月3本目標）

**セッションについて**
- 深掘りチェーンの各ステップ出力はページを閉じると消える（Step 5の構成案のみ保存）
- 読書メモは「一時保存」すると同セッション中はTab2のプロンプトに自動反映
""")

with st.expander("🔁 リバイバル — 過去記事をXで切り取り再拡散"):
    st.markdown("""
**何ができるか**
- 過去記事を「もとやま式つまみ食い」でX投稿に切り取る（3パターン生成）
- 季節・曜日・経過日数でスコアリング → 「今日のおすすめ3本」をサジェスト

**いつ使うか**：新記事を書けない日でも発信を続けたいとき

**スコアの仕組み**：季節キーワード × 曜日 × 経過日数（14日未満は除外・60日以上はボーナス）
""")

with st.expander("💡 アイデア — ネタ管理（Notion連携）"):
    st.markdown("""
**何ができるか**
- Notion「Note投稿用」DBのステータス=アイデアを一覧表示
- アプリから新規アイデアを追加
- 「✏️ 執筆する」で執筆画面にタイトル・メモを引き継いで遷移

**典型フロー**：ふと浮かんだネタを登録 → 後日一覧から「✏️ 執筆する」
""")

with st.expander("📚 ナレッジ — 外部情報の蓄積・分析"):
    st.markdown("""
**2つの蓄積方法**

| 方法 | 用途 |
|---|---|
| Notionインプット分析 | 気になった外部情報をNotionに溜め → `/input-analyze` で3軸スコアリング |
| Gemini Gem取り込み | X投稿・記事・本をGemini Gemで構造化 → アプリに貼り付けて保存 |

**3軸スコア**：Noteプロジェクト / キャリア・仕事 / 発信アイデア（各1〜3）

**インプット分析の実行**：Claude Code で `/input-analyze` を実行（ホーム画面でも経過日数を確認できます）
""")

with st.expander("📊 KPI — 月間目標と進捗可視化"):
    st.markdown("""
**何ができるか**
- 累計記事数 / 今月の投稿本数 / 目標進捗率 を自動集計
- 月次数値（フォロワー・Like・流入・売上）をコピペ入力で履歴化
- 月間投稿カレンダー（投稿日にバッジ表示）

**5月目標**：フォロワー75名 / 月間6本 / 有料記事3本

**データ保存先**：`app/outputs/kpi_history.json`
""")

with st.expander("⚙️ 設定 — プロンプトの閲覧・編集"):
    st.markdown("""
`app/prompts/` 配下の全プロンプトをブラウザから閲覧・編集できます。
記事のトーンや出力ルールを変えたくなったら直接編集。
""")

st.divider()

# ════════════════════════════════════════════
# Tips
# ════════════════════════════════════════════
st.markdown("## 💡 Tips")
st.markdown("""
- **ホーム画面**の「今日のタスク」でインプットDB処理・月末振り返り・投稿進捗を毎回チェック
- 各機能の上部にある `🔄 Notionから再読み込み` ボタンでNotion側の変更を即反映
- セッション状態はブラウザタブを閉じるまで保持（有料記事の深掘りチェーンも同様）
- 執筆画面の `🔄 リセット` ボタンで記事の途中経過をクリア可能
""")
