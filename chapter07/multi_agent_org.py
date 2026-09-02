"""
multi_agent.py - 第7章 A2A：マルチエージェントシステム

複数のエージェントが協力してタスクを完成させる例です。
分析・提案・まとめの3つのエージェントがチームとして働きます。

実行方法: python multi_agent.py
"""

import os
from google.adk.agents import LlmAgent
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# ──────────────────────────────────────────────────────────────────────────────
# サブエージェント【1】：データ分析担当
# ──────────────────────────────────────────────────────────────────────────────
analysis_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="analysis_agent",
    description="データや状況を分析して、現状の課題と問題点を特定する専門エージェント",
    instruction="""
    あなたはデータ分析の専門家です。

    テーマを受け取ったら、以下の形式で分析結果を出力してください：

    ## 【分析結果】
    ### 現状の整理
    （現在の状況を客観的に整理）

    ### 主要な課題（最大3つ）
    1. 課題【1】: （具体的な問題点）
    2. 課題【2】: （具体的な問題点）
    3. 課題【3】: （具体的な問題点）

    ### データから見えること
    （数値や事実に基づいた観察）

    分析は客観的・論理的に行ってください。
    """,
)


# ──────────────────────────────────────────────────────────────────────────────
# サブエージェント【2】：改善提案担当
# ──────────────────────────────────────────────────────────────────────────────
proposal_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="proposal_agent",
    description="分析結果を基に具体的な改善案・解決策を提案する専門エージェント",
    instruction="""
    あなたは改善提案の専門家です。

    分析結果を受け取ったら、以下の形式で改善案を出力してください：

    ## 【改善提案】
    ### 短期的対策（1ヶ月以内に実施可能）
    - 対策【1】: （具体的なアクション）
    - 対策【2】: （具体的なアクション）

    ### 中長期的対策（3〜6ヶ月）
    - 施策【1】: （具体的な取り組み）
    - 施策【2】: （具体的な取り組み）

    ### 期待される効果
    （各対策を実施した場合の期待効果）

    提案は実行可能で具体的なものにしてください。
    """,
)


# ──────────────────────────────────────────────────────────────────────────────
# サブエージェント【3】：レポートまとめ担当
# ──────────────────────────────────────────────────────────────────────────────
summary_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="summary_agent",
    description="分析と提案を統合して、わかりやすいエグゼクティブサマリーを作成する専門エージェント",
    instruction="""
    あなたはレポート作成の専門家です。

    分析結果と改善提案を受け取ったら、経営陣向けの簡潔なまとめを作成してください：

    ## 【エグゼクティブサマリー】
    （2〜3文で全体の要約）

    ## 重要ポイント（3つ）
    ✅ ポイント【1】
    ✅ ポイント【2】
    ✅ ポイント【3】

    ## 最優先アクション
    （今すぐ取り組むべき1つのこと）

    ## まとめ
    （締めくくりの一言）

    ---
    ※ このレポートは AI マルチエージェントシステム（分析・提案・まとめの3エージェント）が協力して作成しました。
    """,
)


# ──────────────────────────────────────────────────────────────────────────────
# コーディネーター（指揮者エージェント）
# A2Aプロトコルでサブエージェントを協調させます
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】A2A（Agent-to-Agent）の実装方法
# │
# │【本ファイル（実行用）】
# │  root_agent = LlmAgent(
# │      ...
# │      sub_agents=[analysis_agent, proposal_agent, summary_agent],
# │  )
# │  # → LlmAgent の sub_agents で、AIが自律的に他エージェントに指示する
# │
# │【教科書のサンプルコード（イメージ）】
# #  # 本格的なA2Aは外部エージェントとHTTPで通信する
# #  from google.adk.tools import AgentTool
# #  remote_agent = AgentTool(agent_url="http://analysis-service/agent")
# #  # または A2A プロトコルの公式SDKを使う
# │
# │【補足説明】
# │  本格的なA2Aはネットワーク越しに別のサービスで動く
# │  エージェントと HTTP で通信する仕組みです。
# │  本ファイルでは同じプロセス内（InProcess）で複数エージェントが
# │  協調するシンプルな実装で概念を学んでいます。
# │  実際のA2A（別サーバー間通信）を試すには、
# │  教科書の AgentTool や A2A SDK の章を参照してください。
# └─────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="coordinator_agent",
    instruction="""
    あなたはマルチエージェントチームのコーディネーター（指揮者）です。

    ユーザーからテーマを受け取ったら、以下の順序でチームを動かします：

    ステップ1: analysis_agent（分析担当）に現状分析を依頼する
    ステップ2: 分析結果を proposal_agent（提案担当）に渡し、改善策を考えさせる
    ステップ3: 分析と提案の両方を summary_agent（まとめ担当）に渡し、レポートを完成させる
    ステップ4: 完成したレポートをユーザーに提示する

    各エージェントの専門性を最大限に活かして、高品質なレポートを作成してください。
    """,
    sub_agents=[analysis_agent, proposal_agent, summary_agent],
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
