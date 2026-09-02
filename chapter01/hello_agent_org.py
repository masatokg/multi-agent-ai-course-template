"""
hello_agent.py - 第1章 最初のAIエージェント

このスクリプトは、Google ADKを使った最初のAIエージェントの例です。
エージェントに話しかけると、AIが返事をしてくれます。

実行方法: python hello_agent.py
"""

import os
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】インポート方法
# │
# │【本ファイル（実行用）】
# │  from google.adk.agents import LlmAgent
# │  from google.adk.runners import InProcessRunner
# │  # │  from google.genai import types
# │
# │【教科書のサンプルコード（イメージ）】
# #  import google.generativeai as genai
# #  from google.adk import Agent
# │
# │【補足説明】
# │  教科書ではライブラリ名・クラス名が簡略表記されているケースがあります。
# │  本ファイルは google-adk の実際の API に合わせた正式な書き方です。
# │  - LlmAgent              : 言語モデルを使うエージェントのクラス
# │  - InProcessRunner       : エージェントを同じプロセス内で動かす実行クラス
# │  - InMemorySessionService: 会話履歴をメモリ上に保持するクラス
# │  - types                 : メッセージ形式（Content/Part）を定義するモジュール
# └─────────────────────────────────────────────────────────────────────────────
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
# エージェントの定義
# 「instruction」がエージェントへの指示文（プロンプト）です
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【2】】エージェントのクラス名・モデル名・変数名
# │
# │【本ファイル（実行用）】
# │  root_agent = LlmAgent(model="gemini-2.5-flash", ...)
# │
# │【教科書のサンプルコード（イメージ）】
# #  agent = Agent(model="gemini-pro", ...)
# │
# │【補足説明】
# │  - クラス名 : 教科書では "Agent" と表記されることがありますが、
# │    ADK の正式クラス名は "LlmAgent" です。
# │  - モデル名 : 本ファイルでは "gemini-2.5-flash" を標準使用します。
# │    ※万が一503エラー（サーバー高負荷）が出た場合は "gemini-3.5-flash" や "gemini-3.7-flash" に変更してください。
# │  - 変数名  : 教科書では "agent" ですが、マルチエージェント構成での
# │    一貫性のため "root_agent" という名前にしています。
# └─────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="hello_agent",
    instruction="""
    あなたは「AIエージェント入門」授業のアシスタントです。
    学生からの質問に、わかりやすく丁寧に答えてください。
    難しい言葉はできるだけ使わず、例え話を交えて説明しましょう。
    """,
)


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

    # ┌─────────────────────────────────────────────────────────────────────────
    # │【教科書との差分【3】】APIキーの設定方法
    # │
    # │【本ファイル（実行用）】
    # │  api_key = os.environ.get("GOOGLE_API_KEY", "")
    # │  # → setup.ps1 で環境変数に保存済みのキーを自動で読み込む
    # │
    # │【教科書のサンプルコード（イメージ）】
    # #  genai.configure(api_key="AIzaxxxxxxxx")   # 直接キーを書く例
    # │
    # │【補足説明】
    # │  教科書ではAPIキーをコードに直接書く例が示されている場合があります。
    # │  しかしAPIキーをコードに書くと、GitHubに公開したときに
    # │  他人に使われてしまう危険があります（セキュリティリスク）。
    # │  本ファイルでは環境変数から読み込む安全な方法を採用しています。
    # │  また ADK では環境変数 GOOGLE_API_KEY を自動で読み取る仕組みが
    # │  あるため、genai.configure() の呼び出しは不要です。
    # └─────────────────────────────────────────────────────────────────────────
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if len(api_key) <= 15:
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        print("  setup.ps1 を実行してAPIキーを設定してください。")
        return

    # ┌─────────────────────────────────────────────────────────────────────────
    # │【教科書との差分【4】】セッションとランナーの初期化
    # │
    # │【本ファイル（実行用）】
    # │  runner = InProcessRunner(agent=root_agent, app_name="hello_agent_app")
    # │  session = runner.session_service.create_session_sync(app_name="hello_agent_app", user_id="student_001")
    # │
    # │【教科書のサンプルコード（イメージ）】
    # #  response = agent.run("こんにちは")   # 簡略1行版
    # │
    # │【補足説明 (google-adk 2.8.0+)】
    # │  最新の ADK では Runner が内部で専用の session_service を管理します。
    # │  `runner.session_service.create_session_sync(...)` からセッションを発行することで
    # │  会話履歴の不一致や Session not found エラーを防止します。
    # └─────────────────────────────────────────────────────────────────────────
    # ランナーの初期化（エージェントを実際に動かす仕組み）
    runner = InProcessRunner(
        agent=root_agent,
        app_name="hello_agent_app",
    )

    # セッションの作成（会話ノートの初期化）
    session = runner.session_service.create_session_sync(
        app_name="hello_agent_app",
        user_id="student_001",
    )

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

        # ┌─────────────────────────────────────────────────────────────────────
        # │【教科書との差分【5】】エージェントへのメッセージ送信とレスポンス受信
        # │
        # │【本ファイル（実行用）】
        # │  for event in runner.run(
        # │      user_id=..., session_id=...,
        # │      new_message=types.Content(role="user",
        # │                               parts=[types.Part(text=user_input)]),
        # │  ):
        # │
        # │【教科書のサンプルコード（イメージ）】
        # #  response = agent.run(user_input)   # シンプルな1行版
        # #  print(response.text)
        # │
        # │【補足説明】
        # │  教科書では簡略化のため agent.run(テキスト) のように
        # │  1行で書かれていることがあります。
        # │  本ファイルでは ADK の正式な API を使っており：
        # │  - types.Content : メッセージの「封筒」（誰から・どんな内容か）
        # │  - types.Part    : メッセージの「中身」（テキスト・画像等）
        # │  - role="user"   : このメッセージはユーザーからのものと明示
        # │  - for event in runner.run(...) : 応答をストリーミングで受け取る
        # │    （長い返答も少しずつ表示できる仕組み）
        # └─────────────────────────────────────────────────────────────────────
        # エージェントに送信して返答を受け取る
        print("AI> ", end="", flush=True)
        try:
            for event in runner.run(
                user_id="student_001",
                session_id=session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)],
                ),
            ):
                # テキスト応答を出力
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(part.text, end="", flush=True)

            print()  # 改行
        except Exception as e:
            print(f"\n  ❌ エラーが発生しました: {e}")
            print("  APIキーが正しいか確認してください。")

        print()


if __name__ == "__main__":
    main()
