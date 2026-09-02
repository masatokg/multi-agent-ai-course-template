"""
hello_agent.py - 第1章 最初のAIエージェント（演習用穴埋めコード）

このスクリプトは、Google ADKを使った最初のAIエージェントの例です。
【1】〜【4】の穴埋め箇所を記述して、エージェントを完成させましょう！

実行方法: python hello_agent.py
"""

import os
from google.adk.agents import LlmAgent
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【1】】AIエージェントの定義
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   Google ADKで最も基本となる「LlmAgent」を作成し、AIのモデル名や役割（プロンプト）を設定します。
#
# ■ 作業指示:
#   LlmAgent() を呼び出し、変数 `root_agent` に代入してください。
#
# ■ 設定する引数:
#   - model       : "gemini-2.0-flash" (使用するAIモデル)
#   - name        : "hello_agent" (エージェントの識別名)
#   - instruction : エージェントへの指示文（「あなたは〜です。〜答えてください。」など）
#
# ■ コードの書き方イメージ:
#   root_agent = LlmAgent(
#       model="gemini-2.0-flash",
#       name="hello_agent",
#       instruction="ここに指示文を書く",
#   )
# ──────────────────────────────────────────────────────────────────────────────

# ↓↓↓ ここに 【穴埋め【1】】 のコードを記述してください ↓↓↓
root_agent = None  # ← None を消して LlmAgent(...) を記述してください


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第1章：最初のAIエージェント")
    print("=" * 60)
    print()
    print("  AIエージェントに話しかけてみましょう！")
    print("  「quit」または「exit」と入力すると終了します。")
    print()

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key.startswith("AIza"):
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        print("  setup.ps1 を実行してAPIキーを設定してください。")
        return

    # ──────────────────────────────────────────────────────────────────────────
    # 【穴埋め【2】】セッションサービスとセッションの作成
    # ──────────────────────────────────────────────────────────────────────────
    # ■ 学習の目的:
    #   エージェントが会話を記憶・管理するための「セッション機能」を初期化します。
    #
    # ■ 作業指示:
    #   1. `session_service = InMemorySessionService()` を作成します。
    #   2. `session = session_service.create_session(...)` を呼び出してセッションを発行します。
    #
    # ■ create_session の引数:
    #   - app_name : "hello_agent_app"
    #   - user_id  : "student_001"
    # ──────────────────────────────────────────────────────────────────────────

    # ↓↓↓ ここに 【穴埋め【2】】 のコードを記述してください ↓↓↓
    session_service = None  # ← InMemorySessionService() のインスタンスを作成
    session = None          # ← session_service.create_session(app_name="hello_agent_app", user_id="student_001") を記述

    # ──────────────────────────────────────────────────────────────────────────
    # 【穴埋め【3】】実行エンジン（ランナー）の初期化
    # ──────────────────────────────────────────────────────────────────────────
    # ■ 学習の目的:
    #   エージェントとセッションを統合し、実際に処理を実行する司令塔「InProcessRunner」を用意します。
    #
    # ■ 作業指示:
    #   InProcessRunner() を作成し、変数 `runner` に代入してください。
    #
    # ■ 設定する引数:
    #   - agent           : root_agent
    #   - app_name        : "hello_agent_app"
    #   - session_service : session_service
    # ──────────────────────────────────────────────────────────────────────────

    # ↓↓↓ ここに 【穴埋め【3】】 のコードを記述してください ↓↓↓
    runner = None  # ← InProcessRunner(...) を記述してください

    print("  ✅ エージェントの準備ができました！")
    print()

    # 会話ループ
    while True:
        try:
            user_input = input("あなた> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.lower() in ("quit", "exit", "終了"):
            print("  👋 終了します。お疲れさまでした！")
            break

        if not user_input:
            continue

        # ──────────────────────────────────────────────────────────────────────
        # 【穴埋め【4】】エージェントへのメッセージ送信とレスポンス表示
        # ──────────────────────────────────────────────────────────────────────
        # ■ 学習の目的:
        #   ユーザーの入力を `types.Content` に包んで `runner.run()` に渡し、
        #   AIからの応答イベントを受け取って逐次表示（ストリーミング出力）します。
        #
        # ■ 作業指示:
        #   1. `runner.run()` を呼び出して for ループでイベントを取り出します。
        #   2. `event.content.parts` からテキストを取り出して `print(part.text, end="", flush=True)` で表示します。
        #
        # ■ runner.run(...) に渡す引数:
        #   - user_id    : "student_001"
        #   - session_id : session.id
        #   - new_message: types.Content(role="user", parts=[types.Part(text=user_input)])
        # ──────────────────────────────────────────────────────────────────────
        print("AI> ", end="", flush=True)
        try:
            # ↓↓↓ ここに 【穴埋め【4】】 のコードを記述してください ↓↓↓
            # 例:
            # for event in runner.run(
            #     user_id="student_001",
            #     session_id=session.id,
            #     new_message=types.Content(
            #         role="user",
            #         parts=[types.Part(text=user_input)],
            #     ),
            # ):
            #     if event.content and event.content.parts:
            #         for part in event.content.parts:
            #             if hasattr(part, "text") and part.text:
            #                 print(part.text, end="", flush=True)
            pass

            print()  # 改行
        except Exception as e:
            print(f"\n  ❌ エラーが発生しました: {e}")
            print("  APIキーが正しいか確認してください。")

        print()


if __name__ == "__main__":
    main()
