"""有料記事制作フロー（読書メモ → 深掘り → 執筆）"""
import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.theme import apply_minimal_theme

apply_minimal_theme()

PAID_CHAIN_PATH = Path(__file__).parent.parent / "data" / "paid_chain_result.json"

# ── session_state 初期化 ──
_PAID_DEFAULTS = {
    "paid_memo": "",
    "paid_context": "",
    "paid_book_title": "",
    "paid_chain_step": 0,
    "paid_chain_outputs": {},   # {step: output_text}
    "paid_chain_saved": False,
}
for k, v in _PAID_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.title("💴 有料記事制作フロー")
st.caption("読書メモ → 深掘りチェーン → 有料執筆の一気通貫ワークフロー")

tab_memo, tab_chain, tab_write = st.tabs(["📖 読書メモ → アジェンダ", "🔍 深掘りチェーン", "✍️ 有料執筆"])

# ════════════════════════════════════════════════════════
# TAB 1: 読書メモ → アジェンダ / 要約
# ════════════════════════════════════════════════════════
with tab_memo:
    st.markdown("### 📖 読書メモをアジェンダ・要約に変換")
    st.caption("Notionに書き溜めた読書メモをここに貼り付け。録音前のアジェンダ or 要約プロンプトを生成します。")

    book_title = st.text_input(
        "本のタイトル",
        value=st.session_state.paid_book_title,
        placeholder="例：ファイブウェイ・ポジショニング戦略",
    )
    memo_text = st.text_area(
        "読書メモ（Notionからコピペ or 直接入力）",
        value=st.session_state.paid_memo,
        height=300,
        placeholder="・付箋メモ\n・気になった箇所\n・自分の感想・疑問など、箇条書きでOK",
    )
    st.caption(f"文字数: {len(memo_text.strip()):,} 文字")

    if st.button("💾 メモを一時保存", disabled=not memo_text.strip()):
        st.session_state.paid_memo = memo_text
        st.session_state.paid_book_title = book_title
        st.success("保存しました（セッション中のみ有効）")

    st.divider()

    if not memo_text.strip():
        st.info("読書メモを入力すると、以下のプロンプトが生成されます。")
    else:
        _book_label = book_title.strip() if book_title.strip() else "この本"

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🎙️ 録音アジェンダを生成")
            _agenda_prompt = f"""以下は「{_book_label}」の読書メモです。

このメモをもとに、私が音声録音するための**アジェンダ（台本案）**を作成してください。

## 出力形式
1. **録音テーマ**（この本から語るべき核心を1文で）
2. **冒頭の問いかけ**（リスナーの共感を引く導入文）
3. **話すべきポイント**（3〜5つの見出し + 各30字程度の説明）
4. **締めのメッセージ**（INFJの読者が持ち帰れる一言）

## 注意
・「日記にならない」こと。個人体験を普遍的な法則に昇華させる方向で設計すること
・録音時間の目安：8〜12分

---
## 読書メモ
{memo_text.strip()}
"""
            st.code(_agenda_prompt, language=None)
            st.caption("↑ コピーして Claude.ai に貼り付け")

        with col_b:
            st.markdown("#### 📋 メモを要約")
            _summary_prompt = f"""以下は「{_book_label}」の読書メモです。

このメモを分析し、有料記事執筆のための素材として整理してください。

## 出力形式
### 1. 核心メッセージ（1文）
### 2. 重要概念・キーワード（3〜5個 + 説明）
### 3. INFJへの応用ポイント（この本の内容が生きづらいINFJにとって何の武器になるか）
### 4. 記事の切り口アイデア（タイトル案3つ）
### 5. 深掘りすべき問い（「深掘りチェーン」で使う問いかけ2〜3個）

---
## 読書メモ
{memo_text.strip()}
"""
            st.code(_summary_prompt, language=None)
            st.caption("↑ コピーして Claude.ai に貼り付け")

# ════════════════════════════════════════════════════════
# TAB 2: 深掘りチェーン
# ════════════════════════════════════════════════════════
with tab_chain:
    st.markdown("### 🔍 深掘りチェーン（5ステップ）")
    st.caption("AIを編集者として機能させ、独自の持論・コンテンツ構成を引き出します。各ステップのプロンプトをコピーして Claude.ai へ。")

    # ── コンテキスト入力（Step 0）──
    with st.expander("⚙️ Step 0：コンテキスト設定（最初に1回だけ）", expanded=(st.session_state.paid_chain_step == 0)):
        _ctx_default = """・目的：生きづらさを抱えるINFJに「余裕」のきっかけを作る
・強み：共感力、物事を構造化する力、内省を言語化する力
・ターゲット：20代のINFJ・内向型。職場や人間関係・人生の目的に疲弊している人"""
        context_input = st.text_area(
            "あなたのコンテキスト（目的・強み・ターゲット）",
            value=st.session_state.paid_context or _ctx_default,
            height=130,
        )
        _book_for_chain = st.text_input(
            "本のタイトル（チェーン用）",
            value=st.session_state.paid_book_title,
            key="chain_book_title",
        )
        _step0_prompt = f"""あなたは優秀な編集者であり、私の壁打ち相手です。
これから、私が読んだ本「{_book_for_chain or '（本タイトル）'}」のデータを提供します。目的は「単なる要約」ではなく、この内容から私独自の「持論」を引き出し、INFJや生きづらさを抱える20代に向けたオリジナルコンテンツを作成することです。
以下の私のコンテキストをインプットした上で、「了解しました」とだけ返答してください。

【私のコンテキスト】
{context_input}"""
        st.code(_step0_prompt, language=None)
        if st.button("✅ コンテキストを保存してStep 1へ", type="primary"):
            st.session_state.paid_context = context_input
            st.session_state.paid_book_title = _book_for_chain
            st.session_state.paid_chain_step = max(st.session_state.paid_chain_step, 1)
            st.rerun()

    # ── Step 1〜5 ──
    _CHAIN_STEPS = [
        {
            "label": "Step 1：構造化・キーワード抽出",
            "icon": "🗂️",
            "desc": "本の全体像を把握し、独自概念・キーワードを抽出します。",
            "prompt_template": """以下のテキスト（文字起こしまたは読書メモ）を分析してください。

1. このテキストに含まれる実践的なノウハウを、体系的かつ網羅的に構造化して要約してください。
2. この本ならではの「独自の考え方」や「象徴的なキーワード（独自フレームワーク等）」を3〜5個抽出し、なぜそれが重要かを解説してください。

【テキスト】
{memo}""",
        },
        {
            "label": "Step 2：ターゲット視点のパラダイムシフト",
            "icon": "💡",
            "desc": "一般論をINFJ・内向型にとっての「救い・武器」に翻訳します。",
            "prompt_template": """抽出した内容を、私のターゲット（内向型・INFJ）の視点で読み解いてください。
一般的なノウハウの中で、彼らにとって特に「有利になること」「既存の強みを活かせること」「自信のなさの支えになること」「目から鱗になるような視点の転換」を5つ提示してください。
それぞれ、「一般的な捉え方」と「ターゲットにとっての新しい解釈」を対比させて書いてください。""",
        },
        {
            "label": "Step 3：自分の軸への当てはめ（CEP設計）",
            "icon": "🎯",
            "desc": "本の内容と自分の活動・強みを強制的に結びつけます。",
            "prompt_template": """Step2で提示した解釈を、最初にインプットした「私のコンテキスト（強みや目的）」に当てはめて分析します。

1. この本で語られている重要な法則や概念を、私自身の活動やセルフブランディングに適用すると、どのような形になりますか？
2. この内容を踏まえて、私がターゲットから「選ばれる状況（CEP＝〇〇な時にこの人に頼ろうと思われる場面）」を3つ設計してください。""",
        },
        {
            "label": "Step 4：持論の言語化",
            "icon": "✏️",
            "desc": "独自コンテンツの材料となる「問い」と「持論」を完成させます。",
            "prompt_template": """ここまでの内容を元に、私が独自コンテンツを作るための材料を整理します。

1. このテーマについて、ターゲットの心を深く刺し、私の内省を引き出すような「本質的な問いかけ」を5つ作成してください。
2. 私の強みや目的（インプットしたコンテキスト）に基づき、その5つの問いかけに対する「私ならではの持論（アンサー）」を言語化してください。ただの共感ではなく、「構造化や仕組み化」といった私の独自性（スパイス）を必ず含めてください。""",
        },
        {
            "label": "Step 5：コンテンツ構成案の作成",
            "icon": "📐",
            "desc": "持論を有料記事の構成案としてパッケージ化します。（この出力を保存して執筆へ）",
            "prompt_template": """ありがとうございます。最後に、ここまでの要素（Step1の独自キーワード、Step2の目から鱗ポイント、Step4の持論）をすべて統合し、有料Note記事用の構成案を作成してください。

以下の構成で出力してください。
・タイトル案（3つ。独自キャッチーワードを必ず1つ含めること）
・【起】導入（ターゲットの痛みの代弁と、一般的な誤解の提示）
・【承】視点の転換（この本から得た新しい解釈・目から鱗ポイント）
・【転】独自の持論（私の強みを活かした解決策・構造化の提示）
・【結】結論（ターゲットに「余裕」を与えるメッセージ）
・ペイウォール境界線（どこまでを無料にするか）""",
        },
    ]

    current_step = st.session_state.paid_chain_step

    for i, step_def in enumerate(_CHAIN_STEPS):
        step_num = i + 1
        is_current = (current_step == step_num)
        is_done = (current_step > step_num) or (str(step_num) in st.session_state.paid_chain_outputs)

        label = f"{'✅' if is_done else ('▶️' if is_current else '○')} {step_def['icon']} {step_def['label']}"
        with st.expander(label, expanded=is_current):
            st.caption(step_def["desc"])

            # プロンプト生成
            _memo = st.session_state.paid_memo or "（Tab1で読書メモを入力してください）"
            _prompt = step_def["prompt_template"].replace("{memo}", _memo)
            st.code(_prompt, language=None)
            st.caption("↑ コピーして Claude.ai に貼り付け、返答を以下に記録")

            # 出力記録欄
            _saved_output = st.session_state.paid_chain_outputs.get(str(step_num), "")
            _output = st.text_area(
                f"Claude の返答（Step {step_num}）",
                value=_saved_output,
                height=180,
                placeholder="AIの返答をここに貼り付け（任意・参照用）",
                key=f"chain_output_{step_num}",
            )

            _btn_col1, _btn_col2 = st.columns([3, 1])
            with _btn_col1:
                if step_num < 5:
                    if st.button(f"次へ → Step {step_num + 1}", key=f"chain_next_{step_num}", type="primary"):
                        if _output.strip():
                            st.session_state.paid_chain_outputs[str(step_num)] = _output
                        st.session_state.paid_chain_step = step_num + 1
                        st.rerun()
                else:
                    # Step 5: 保存ボタン
                    if st.button("💾 構成案を保存して執筆へ", key="chain_save", type="primary", disabled=not _output.strip()):
                        st.session_state.paid_chain_outputs["5"] = _output
                        _save_data = {
                            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "book_title": st.session_state.paid_book_title,
                            "context": st.session_state.paid_context,
                            "memo": st.session_state.paid_memo,
                            "outline": _output,
                        }
                        PAID_CHAIN_PATH.write_text(
                            json.dumps(_save_data, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        st.session_state.paid_chain_saved = True
                        st.success("構成案を保存しました。「✍️ 有料執筆」タブへ進んでください。")

            with _btn_col2:
                if _output.strip() and st.button("メモ保存", key=f"chain_memo_{step_num}"):
                    st.session_state.paid_chain_outputs[str(step_num)] = _output
                    st.success("✓")

    # リセット
    st.divider()
    if st.button("🔄 チェーンをリセット"):
        st.session_state.paid_chain_step = 0
        st.session_state.paid_chain_outputs = {}
        st.session_state.paid_chain_saved = False
        st.rerun()

# ════════════════════════════════════════════════════════
# TAB 3: 有料執筆
# ════════════════════════════════════════════════════════
with tab_write:
    st.markdown("### ✍️ 有料記事 執筆プロンプト")
    st.caption("深掘りチェーンの構成案をもとに、有料記事を執筆します。")

    # 構成案の読み込み
    _outline = ""
    if st.session_state.paid_chain_outputs.get("5"):
        _outline = st.session_state.paid_chain_outputs["5"]
    elif PAID_CHAIN_PATH.exists():
        _saved = json.loads(PAID_CHAIN_PATH.read_text(encoding="utf-8"))
        _outline = _saved.get("outline", "")
        if _outline:
            st.info(f"保存済みの構成案を読み込みました（{_saved.get('saved_at', '')} / {_saved.get('book_title', '')}）")

    if not _outline:
        st.warning("深掘りチェーン（Tab2）のStep 5を完了・保存すると、ここに構成案が読み込まれます。")
        _outline = st.text_area("または、構成案を直接貼り付け", height=200, placeholder="構成案をここに貼り付けてもOKです")

    # 文字起こし入力
    st.divider()
    _paid_transcription = st.text_area(
        "録音の文字起こし（独自視点の録音）",
        value=st.session_state.get("paid_transcription", ""),
        height=200,
        placeholder="録音データの文字起こしをここに貼り付けてください",
        key="paid_transcription_input",
    )
    if st.button("💾 文字起こしを保存"):
        st.session_state["paid_transcription"] = _paid_transcription

    _transcription = st.session_state.get("paid_transcription", "") or _paid_transcription

    st.divider()

    # 執筆ステップ
    write_step = st.session_state.get("paid_write_step", 0)
    _write_steps = ["① 内容読み込ませ", "② 前半執筆（無料エリア）", "③ 後半執筆（有料エリア）"]

    for i, label in enumerate(_write_steps):
        is_active = (write_step == i)
        with st.expander(f"{'▶️' if is_active else '○'} {label}", expanded=is_active):
            if i == 0:
                _prompt = f"""これから有料記事の執筆を行いますが、まずは以下の「構成案」と「文字起こし原文」を読み込んで内容を理解してください。
※まだ記事は執筆しないでください。内容を完璧に理解したら「理解しました。執筆指示を待機します。」とだけ返答してください。

---
## 【入力データA】決定した構成案
{_outline or "（構成案を入力してください）"}

---
## 【入力データB】文字起こし原文（重要）
{_transcription or "（文字起こしを入力してください）"}
※ここに含まれる「具体的なエピソード」「話し手の感情」「独特な言い回し」を執筆時に反映させるため、必ず参照してください。"""
            elif i == 1:
                _prompt = """# 役割
あなたは、事象を論理的かつ分かりやすく構造化するプロフェッショナルなコラムニストです。決定した構成案の「導入」から「第2章（事象の分析）」までを執筆してください。

# 文体とトーン
・「〜だ・〜である」調（あるいは、知的で静かな「です・ます」調）。
・感情的になりすぎず、理知的でフラットなトーン。ただし、時折「INFJの心の声（本音や少しの毒）」を混ぜて共感を誘うこと。
・専門用語やフレームワークを用いる場合は、誰にでもわかるように噛み砕いて説明すること。

# 導入のルール
日常の「あるある」な悩みからスタートし、「なぜ私たちはこれで消耗してしまうのか？」という問いを立てて、読者の知的好奇心を刺激してください。
また、前のステップで決定した「独自のキャッチーなキーワード」を必ず登場させてください。

# 結びのルール（有料線への引き）
第2章の最後は、「なぜ苦しいのかは分かった。では、具体的に明日からどうやって自分を守ればいいのか？ 次の章で、その具体的な生存戦略（処方箋）を解説する。」というように、読者の期待感を最高潮に高める「寸止め」の状態で文章を終えてください。（※ここで無料/有料の境界線を引くため）"""
            else:
                _prompt = """# 役割
引き続き、記事の後半（第3章〜結論、および末尾の案内まで）を執筆してください。ここは、有料で読んでくれた読者に「明日から使える武器」を手渡す重要なパートです。

# 展開のルール
第3章では、論理的な解説を踏まえた上で、「とはいえ、私たちINFJにとっては〇〇だから実行するのが難しい」という「実践における壁」に軽く寄り添ってください。

# 結論の書き方
精神論は排除し、「明日、職場でこのシチュエーションになったら、心の中でこう唱えよう」「具体的にこの行動だけを変えよう」という、極めて実用的でハードルの低いアクションプランを提示してください。
※読者がスマホで拾い読みしやすいように、具体的な手順は「箇条書き」や「太字」を効果的に使ってください。

# 末尾（マネタイズ・ファン化）
1. おすすめ書籍の紹介：「今回の視点を養うのに役立った本」として関連書籍1冊を紹介する文章（後でAmazonリンクを挿入）
2. メンバーシップへの招待：「この記事のような生存戦略を、よりクローズドな空間で共有しています」というニュアンスで静かに案内（煽り厳禁）"""

            st.code(_prompt, language=None)
            st.caption("↑ コピーして Claude.ai に貼り付け")

            if i < 2:
                if st.button(f"次へ → {_write_steps[i + 1]}", key=f"write_next_{i}", type="primary"):
                    st.session_state["paid_write_step"] = i + 1
                    st.rerun()
