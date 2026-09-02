import os
import sys
import warnings
import logging

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
try:
    from google.adk.runners import InMemoryRunner as InProcessRunner
except ImportError:
    try:
        from google.adk.runners import Runner as InProcessRunner
    except ImportError:
        from google.adk.runners import InProcessRunner
from google.genai import types

load_dotenv(override=True)


os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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


os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【1】】3つの専門サブエージェントの作成
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   複雑なタスク（分析・提案・まとめ）を1つのプロンプトで処理させるのではなく、
#   各分野の「専門エージェント（SubAgent）」に分割して役割分担させます。
#
# ■ 作業指示:
#   以下の3つのエージェントインスタンスを作成してください：
#   1. `analysis_agent` : データ・状況の分析を担当
#   2. `proposal_agent` : 改善案・対策の提案を担当
#   3. `summary_agent`  : 経営陣向けの最終レポートまとめを担当
#
# ■ 記述例:
#   analyzer = LlmAgent(
#       model="gemini-3.5-flash",
#       name="data_analyzer",
#       instruction="データの分析・集計を担当します。",
#   )
# ──────────────────────────────────────────────────────────────────────────────

# ↓↓↓ ここに 【穴埋め【1】】 のコード（3つのサブエージェント）を記述してください ↓↓↓
analysis_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="analysis_agent",
    description="現状の課題と問題点を特定する専門エージェント",
    instruction="あなたはデータ分析の専門家です。現状の整理と課題を出力してください。",
)

proposal_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="proposal_agent",
    description="分析結果に基づいた改善案を提示する専門エージェント",
    instruction="あなたは戦略コンサルタントです。分析結果に対して、具体的で実現可能な改善策を提案してください。",
)

summary_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="summary_agent",
    description="経営陣向けの最終レポートを作成する専門エージェント",
    instruction="あなたは編集者です。分析結果と改善策を統合し、経営陣に提示する簡潔で説得力のあるレポートを作成してください。",
)


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【2】】指揮者（コーディネーター）エージェントとチーム編成
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   ユーザーと対話し、上記3つのサブエージェントに順番に指示を出して
#   最終レポートを完成させるリーダーエージェント（coordinator_agent）を作成します。
#
# ■ 作業指示:
#   `root_agent` の `sub_agents` 引数に `[analysis_agent, proposal_agent, summary_agent]`
#   の3つをセットしてください。
# ──────────────────────────────────────────────────────────────────────────────

root_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="coordinator_agent",
    instruction="""
    あなたはマルチエージェントチームのコーディネーター（指揮者）です。

    ユーザーからテーマを受け取ったら、以下の順序でチームを動かします：
    ステップ1: analysis_agent（分析担当）に現状分析を依頼する
    ステップ2: 分析結果を proposal_agent（提案担当）に渡し、改善策を考えさせる
    ステップ3: 分析と提案の両方を summary_agent（まとめ担当）に渡し、レポートを完成させる
    ステップ4: 完成したレポートをユーザーに提示する
    """,
    # ↓↓↓ ここに 【穴埋め【2】】 の sub_agents=[...] 引数を記述してください ↓↓↓
)


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第7章：A2A マルチエージェントシステム デモ")
    print("=" * 60)
    print()
    print("  このデモでは、3つのエージェントがチームとして協力します：")
    print("  🔍 分析エージェント  → 現状と課題を分析")
    print("  💡 提案エージェント  → 改善案を提案")
    print("  📋 まとめエージェント → 報告書を作成")
    print()
    print("  ビジネス課題や改善したいテーマを入力してください。")
    print("  例: 「社内の会議が多すぎる問題」「ECサイトのカート離脱率が高い」")
    print()
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
        app_name="multi_agent_app",
    )
    session = runner.session_service.create_session_sync(
        app_name="multi_agent_app",
        user_id="student_001",
    )

    print("  ✅ マルチエージェントチームの準備ができました！")
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
        print("  🔄 3つのエージェントが協力してレポートを作成中...")
        print("     分析 → 提案 → まとめ の順番で処理します。")
        print("     （少々お時間がかかります）")
        print()

        # エージェントに送信して返答を受け取る（503エラー自動3回リトライ＆切り替え機能付き）
        # エージェントに送信して返答を受け取る（503/429エラー自動対応機能付き）
        # エージェントに送信して返答を受け取る（503/429エラー自動対応＆スタックトレース非表示機能付き）
        # エージェントに送信して返答を受け取る（リアルタイム・ストリーミング出力 & 429/503エラー対応）
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
                # ── 429エラー（利用制限オーバー）対応 ──────────────────
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
                    print("\n  🚨 【429エラー（利用制限上限到達 / Quota Exceeded）が発生しました】")
                    print("  ご使用中のAPIキーのリクエスト制限（一日の上限）に達しました。")
                    print("  Google AI Studio (https://aistudio.google.com/) で「新しいプロジェクト」を作成し、")
                    print("  自分専用の代替APIキーを発行して以下に入力してください。\n")
                    try:
                        new_key = input("  🔑 新しい GOOGLE_API_KEY を入力してください: ").strip()
                    except (KeyboardInterrupt, EOFError):
                        break
                    
                    if len(new_key) > 15:
                        os.environ["GOOGLE_API_KEY"] = new_key
                        try:
                            with open(".env", "w", encoding="utf-8") as f:
                                f.write(f"GOOGLE_API_KEY={new_key}\n")
                        except Exception:
                            pass
                        print("  ✅ APIキーを更新しました！会話を自動的に再開します...\n")
                        continue
                    else:
                        print("  ❌ APIキーの形式が正しくありません。\n")
                        break

                # ── 503エラー（サーバー高負荷・混雑）対応 ────────────────
                elif "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str:
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