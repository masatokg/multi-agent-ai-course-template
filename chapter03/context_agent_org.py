"""
context_agent.py - 第3章 Context Engineering & Agent Skills

プロンプト設計とサブエージェントの例です。
「調査担当」と「執筆担当」の2つのサブエージェントが協力してレポートを作ります。

実行方法: python context_agent.py
"""

import os
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
# サブエージェント【1】：調査担当
# プロンプト（instruction）を具体的に書くことで、役割が明確になります
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】サブエージェントの定義方法
# │
# │【本ファイル（実行用）】
# │  research_agent = LlmAgent(
# │      model="gemini-3.5-flash",
# │      name="research_agent",
# │      description="...",   ← sub_agentsで使う場合は description が重要
# │      instruction="...",
# │  )
# │
# │【教科書のサンプルコード（イメージ）】
# #  research_agent = Agent(
# #      name="research_agent",
# #      instruction="...",
# #  )
# │
# │【補足説明】
# │  サブエージェントを親エージェント（orchestrator）の sub_agents に
# │  登録する場合、"description" 引数が重要です。
# │  親エージェントは description を読んで「このエージェントに何を頼むべきか」
# │  を判断します。教科書では省略されている場合がありますが、
# │  実際の動作の安定性のために追加しています。
# └─────────────────────────────────────────────────────────────────────────────
research_agent = LlmAgent(
    model="gemini-3.6-flash",
    name="research_agent",
    instruction="""
    あなたはリサーチ専門のエージェントです。

    ユーザーからテーマを受け取ったら、以下の構造でリサーチ結果をまとめてください：

    ## テーマ概要
    （テーマを1〜2文で説明）

    ## 主要なポイント（3つ）
    1. （ポイント1）
    あなたは最新テクノロジーの調査専門のエージェントです。
    ユーザーからテーマを受け取ったら、重要なキーポイントを3〜5個にまとめて抽出してください。
    回答は箇条書きで、事実のみを簡潔に記述してください。
    """,
)


# ──────────────────────────────────────────────────────────────────────────────
# サブエージェント【2】：執筆担当
# ──────────────────────────────────────────────────────────────────────────────
writer_agent = LlmAgent(
    model="gemini-3.6-flash",
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
# オーケストレーター（指揮者エージェント）
# サブエージェントを組み合わせて、タスクを分担させます
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【2】】sub_agents によるマルチエージェント構成
# │
# │【本ファイル（実行用）】
# │  root_agent = LlmAgent(
# │      ...
# │      sub_agents=[research_agent, writer_agent],
# │  )
# │
# │【教科書のサンプルコード（イメージ）】
# #  # SequentialAgent を使う例（教科書によって異なる）
# #  from google.adk.agents import SequentialAgent
# #  pipeline = SequentialAgent(
# #      sub_agents=[research_agent, writer_agent]
# #  )
# │
# │【補足説明】
# │  教科書では SequentialAgent（順番に実行）や ParallelAgent（並列実行）を
# │  使った例が紹介されている場合があります。
# │  本ファイルでは LlmAgent の sub_agents に渡す方法を採用しています。
# │  この方法では、親エージェントが自分でサブエージェントの実行順を判断します
# │  （より柔軟ですが、SequentialAgent より動作が「AIの判断依存」になります）。
# └─────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    model="gemini-3.6-flash",
    name="orchestrator_agent",
    instruction="""
    あなたはレポート作成チームのリーダーです。

    ユーザーからテーマを受け取ったら：
    1. research_agent（調査担当）に詳細なリサーチを依頼する
    2. その結果を writer_agent（執筆担当）に渡し、わかりやすい文章に変換させる
    3. 完成したレポートをユーザーに提示する

    チーム全体の品質に責任を持ってください。
    """,
    sub_agents=[research_agent, writer_agent],
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
    session = runner.runner.session_service.create_session_sync(
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

        try:
            for event in runner.run(
                user_id="student_001",
                session_id=session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=f"「{user_input}」についてレポートを作成してください。")],
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
