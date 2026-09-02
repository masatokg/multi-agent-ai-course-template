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
# │  root_agent = LlmAgent(model="gemini-3.5-flash", ...)
# │
# │【教科書のサンプルコード（イメージ）】
# #  agent = Agent(model="gemini-pro", ...)
# │
# │【補足説明】
# │  - クラス名 : 教科書では "Agent" と表記されることがありますが、
# │    ADK の正式クラス名は "LlmAgent" です。
# │  - モデル名 : 本ファイルでは "gemini-3.5-flash" を標準使用します。
# │    ※万が一503エラー（サーバー高負荷）が出た場合は "gemini-3.5-flash" や "gemini-3.7-flash" に変更してください。
# │  - 変数名  : 教科書では "agent" ですが、マルチエージェント構成での
# │    一貫性のため "root_agent" という名前にしています。
# └─────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    model="gemini-3.5-flash",
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
        # エージェントに送信して返答を受け取る（503/429エラー自動対応機能付き）
        # エージェントに送信して返答を受け取る（503/429エラー自動対応＆スタックトレース非表示機能付き）
        success = False
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print("AI> ", end="", flush=True)
                
                # ADK内部の生のTraceback出力を一時遮断
                import io, sys, contextlib
                stderr_buffer = io.StringIO()
                with contextlib.redirect_stderr(stderr_buffer):
                    events = list(runner.run(
                        user_id="student_001",
                        session_id=session.id,
                        new_message=types.Content(
                            role="user",
                            parts=[types.Part(text=user_input)],
                        ),
                    ))
                
                for event in events:
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
                        # .env にも保存
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
