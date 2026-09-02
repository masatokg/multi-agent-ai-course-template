"""
multi_agent.py - 第7章 A2A：マルチエージェントシステム（演習用穴埋めコード）

複数のエージェントが協力してタスクを完成させる例です。
【1】〜【2】の穴埋め箇所を記述して、3つの専門エージェントチームを編成しましょう！

実行方法: python multi_agent.py
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv(override=True)


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
#       model="gemini-2.5-flash",
#       name="data_analyzer",
#       instruction="データの分析・集計を担当します。",
#   )
# ──────────────────────────────────────────────────────────────────────────────

# ↓↓↓ ここに 【穴埋め【1】】 のコード（3つのサブエージェント）を記述してください ↓↓↓
analysis_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="analysis_agent",
    description="現状の課題と問題点を特定する専門エージェント",
    instruction="あなたはデータ分析の専門家です。現状の整理と課題を出力してください。",
)

proposal_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="proposal_agent",
    description="分析結果に基づいた改善案を提示する専門エージェント",
    instruction="あなたは戦略コンサルタントです。分析結果に対して、具体的で実現可能な改善策を提案してください。",
)

summary_agent = LlmAgent(
    model="gemini-2.5-flash",
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
    model="gemini-2.5-flash",
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
    if not api_key.startswith("AIza"):
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        return

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="multi_agent_app",
        user_id="student_001",
    )

    runner = InProcessRunner(
        agent=root_agent,
        app_name="multi_agent_app",
        session_service=session_service,
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

        try:
            for event in runner.run(
                user_id="student_001",
                session_id=session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=f"「{user_input}」について、チームでレポートを作成してください。")],
                ),
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(part.text, end="", flush=True)

            print()
        except Exception as e:
            print(f"\n  ❌ エラー: {e}")

        print()


if __name__ == "__main__":
    main()
