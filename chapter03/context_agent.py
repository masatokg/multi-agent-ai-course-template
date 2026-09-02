import os
import sys
import warnings
import logging

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.WARNING)

import warnings
warnings.filterwarnings("ignore")
"""
context_agent.py - 第3章 Context Engineering & Agent Skills（演習用穴埋めコード）

プロンプト設計とサブエージェントの例です。
「調査担当」と「執筆担当」の2つのサブエージェントが協力してレポートを作ります。
【1】〜【2】の穴埋め箇所を記述して、マルチエージェント連携を完成させましょう！

実行方法: python context_agent.py
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
try:
    from google.adk.runners import InMemoryRunner as InProcessRunner
except ImportError:
    try:
        from google.adk.runners import Runner as InProcessRunner
    except ImportError:
        from google.adk.runners import InProcessRunner
from google.genai import types

load_dotenv(override=True)

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【1】】サブエージェント【1】（調査担当）の定義
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   特定の役割に特化した「専門エージェント」を作成します。
#   プロンプト（instruction）に出力フォーマットの構造を指定することで、
#   後続の執筆エージェントが受け取りやすい高品質なリサーチ結果を生成させます。
#
# ■ 作業指示:
#   `research_agent = LlmAgent(...)` の定義を完成させてください。
#   `instruction` には「テーマ概要」「主要なポイント（3つ）」「注意点」の3つの見出しを含めて
#   リサーチ結果をまとめるよう指示してください。
#
# ■ 記述例:
#   research_agent = LlmAgent(
#       model="gemini-3.5-flash",
#       name="research_agent",
#       instruction="""
#       あなたはリサーチ専門のエージェントです。
#       以下の構造でリサーチ結果をまとめてください：
#       ## テーマ概要
#       ## 主要なポイント（3つ）
#       ## 注意点
#       """,
#   )
# ──────────────────────────────────────────────────────────────────────────────

# ↓↓↓ ここに 【穴埋め【1】】 のコードを記述してください ↓↓↓
research_agent = None  # ← LlmAgent(...) を記述して研究用エージェントを作成してください


# ──────────────────────────────────────────────────────────────────────────────
# サブエージェント【2】：執筆担当（完成済み）
# ──────────────────────────────────────────────────────────────────────────────
writer_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="writer_agent",
    instruction="""
    あなたはわかりやすい文章を書く専門のエージェントです。

    調査結果を受け取ったら、高校生でも理解できるような文章に変換してください。

    ルール：
    - 専門用語には必ず説明を加える（例：「〇〇（専門用語の説明）」）
    - 箇条書きよりも自然な文章を使う
    - 具体的な例えを1つ以上含める
    - 全体を400字程度にまとめる
    """,
)


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【2】】親エージェント（オーケストレーター）の定義とサブエージェント登録
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   複数の専門エージェントを束ねる「親エージェント（orchestrator）」を作成します。
#   `sub_agents` 引数に子エージェントのリストを渡すことで、親AIが自律的に
#   「どのタスクを誰に任せるか」を判断して順番に呼び出します。
#
# ■ 作業指示:
#   `root_agent` の定義において、`sub_agents` 引数を追加し、
#   `[research_agent, writer_agent]` を渡してください。
#
# ■ 記述例:
#   root_agent = LlmAgent(
#       model="gemini-3.5-flash",
#       name="orchestrator_agent",
#       instruction="...",
#       sub_agents=[research_agent, writer_agent],
#   )
# ──────────────────────────────────────────────────────────────────────────────

# ↓↓↓ ここに 【穴埋め【2】】 の sub_agents=[...] 引数を記述してください ↓↓↓
root_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="orchestrator_agent",
    instruction="""
    あなたはレポート作成チームのリーダーです。

    ユーザーからテーマを受け取ったら：
    1. research_agent（調査担当）に詳細なリサーチを依頼する
    2. その結果を writer_agent（執筆担当）に渡し、わかりやすい文章に変換させる
    3. 完成したレポートをユーザーに提示する

    チーム全体の品質に責任を持ってください。
    """,
    # sub_agents=[research_agent, writer_agent] を追加する
)


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第3章：Context Engineering & Agent Skills")
    print("=" * 60)
    print()
    print("  このデモでは、2つのエージェントが協力してレポートを作ります：")
    print("  📚 調査担当エージェント → テーマをリサーチ")
    print("  ✍️  執筆担当エージェント → わかりやすく文章化")
    print()
    print("  テーマを入力してください（例: 「機械学習とは」「量子コンピュータ」）")
    print("  「quit」と入力すると終了します。")
    print()

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if len(api_key) <= 15:
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        return

    # 💡 【重要：google-adk 2.8.0以降のセッション管理仕様】
    # 最新の google-adk では Runner（司令塔）が内部で専用の session_service を管理します。
    # `runner.session_service.create_session_sync(...)` からセッションを発行することで
# 会話履歴の不一致や Session not found エラーを防止します。
    runner = InProcessRunner(
        agent=root_agent,
        app_name="context_agent_app",
    )
    session = runner.session_service.create_session_sync(
        app_name="context_agent_app",
        user_id="student_001",
    )

    print("  ✅ エージェントチームの準備ができました！")
    print()

    while True:
        try:
            user_input = input("テーマ> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.lower() in ("quit", "exit", "終了"):
            print("  👋 終了します。お疲れさまでした！")
            break

        if not user_input:
            continue

        print()
        print("  📝 レポートを作成中です（少々お待ちください）...")
        print()

        # エージェントに送信して返答を受け取る（503エラー自動3回リトライ＆切り替え機能付き）
        success = False
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print("AI> ", end="", flush=True)
                for event in runner.run(
                    user_id="student_001",
                    session_id=session.id,
                    new_message=types.Content(
                        role="user",
                        parts=[types.Part(text=user_input)],
                    ),
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                print(part.text, end="", flush=True)
                print()  # 改行
                success = True
                break
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str:
                    print(f"\n  ⚠️ 503エラー検出（サーバー高負荷・混雑）。自動リトライ中... ({attempt}/{max_retries})")
                    if attempt < max_retries:
                        import time
                        time.sleep(2)
                        continue
                    else:
                        print("\n  🚨 【503エラー（サーバー高負荷・混雑）が発生しました】")
                        target_agent = root_agent if 'root_agent' in locals() else (agent if 'agent' in locals() else None)
                        curr_model = getattr(target_agent, 'model', 'gemini-3.5-flash') if target_agent else 'gemini-3.5-flash'
                        print(f"  現在設定中のモデル [{curr_model}] は現在Google側でアクセスが集中しています。")
                        print("  以下から代替モデルを選択してください：")
                        print("    [1] gemini-2.5-flash （推奨・超高速・高安定）")
                        print("    [2] gemini-3.7-flash （最新モデル）")
                        print("    [3] 別のモデル名を手動入力")
                        try:
                            choice = input("  選択肢番号を入力してください (1/2/3): ").strip()
                        except (KeyboardInterrupt, EOFError):
                            break
                        if choice == "2":
                            new_model = "gemini-3.7-flash"
                        elif choice == "3":
                            new_model = input("  モデル名を入力: ").strip()
                        else:
                            new_model = "gemini-2.5-flash"

                        if target_agent:
                            target_agent.model = new_model
                        print(f"  🔄 モデルを [{new_model}] に切り替えました。会話を再開します...\n")
                else:
                    print(f"\n  ❌ エラーが発生しました: {e}")
                    print("  APIキーが正しいか確認してください。\n")
                    break


if __name__ == "__main__":
    main()
