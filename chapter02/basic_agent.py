"""
basic_agent.py - 第2章 ツール付きエージェント（演習用穴埋めコード）

エージェントに「計算ツール」と「天気取得ツール（ダミー）」を持たせた例です。
【1】〜【2】の穴埋め箇所を記述して、ツール呼び出しが可能なエージェントを完成させましょう！

実行方法: python basic_agent.py
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
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv(override=True)

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



# ──────────────────────────────────────────────────────────────────────────────
# ツールの定義
# Pythonの関数をそのままエージェントのツールとして使えます
# ──────────────────────────────────────────────────────────────────────────────

def calculate(expression: str) -> dict:
    """
    数式を計算します。

    Args:
        expression: 計算したい数式（例: "100 * 3 / 2", "2 ** 10"）

    Returns:
        計算結果を含む辞書
    """
    # ──────────────────────────────────────────────────────────────────────────
    # 【穴埋め【1】】ツール関数の処理と戻り値の実装
    # ──────────────────────────────────────────────────────────────────────────
    # ■ 学習の目的:
    #   ADKのツール関数は、実行結果を「辞書（dict）」形式で返すのがルールです。
    #   AIは返された辞書のキーと値を見て、結果を人間にわかりやすく解説します。
    #
    # ■ 作業指示:
    #   1. `try` ブロックの中で `eval(expression)` を実行し、結果を `result` に入れます。
    #   2. 成功時は `{"status": "success", "expression": expression, "result": result}` を返します。
    #   3. 例外発生時（`except`）は `{"status": "error", "expression": expression, "error": str(e)}` を返します。
    #
    # ■ コードの書き方イメージ:
    #   try:
    #       result = eval(expression)
    #       return {"status": "success", "expression": expression, "result": result}
    #   except Exception as e:
    #       return {"status": "error", "expression": expression, "error": str(e)}
    # ──────────────────────────────────────────────────────────────────────────

    # ↓↓↓ ここに 【穴埋め【1】】 のコードを記述してください ↓↓↓
    pass


def get_weather(city: str) -> dict:
    """
    指定した都市の天気を取得します（デモ用ダミーデータ）。

    Args:
        city: 都市名（例: "Tokyo", "Osaka"）

    Returns:
        天気情報を含む辞書
    """
    weather_data = {
        "Tokyo":   {"temperature": 28, "condition": "晴れ", "humidity": 65},
        "Osaka":   {"temperature": 30, "condition": "曇り", "humidity": 70},
        "Fukuoka": {"temperature": 32, "condition": "雨",   "humidity": 85},
        "Sapporo": {"temperature": 20, "condition": "晴れ", "humidity": 55},
    }

    city_data = weather_data.get(city, weather_data.get("Tokyo"))
    return {
        "status": "success",
        "city": city,
        "temperature": city_data["temperature"],
        "condition": city_data["condition"],
        "humidity": city_data["humidity"],
        "note": "※これはデモ用のダミーデータです",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【2】】エージェントへのツール登録
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   作成したPython関数を `FunctionTool(func=関数名)` でラップし、
#   `LlmAgent` の `tools` 引数に渡すことで、AIが自律的にツールを選択・実行できるようにします。
#
# ■ 作業指示:
#   `root_agent` の定義において、`tools` 引数を追加し、`calculate` と `get_weather` を登録してください。
#
# ■ 登録の書き方イメージ:
#   tools=[
#       FunctionTool(func=calculate),
#       FunctionTool(func=get_weather),
#   ]
# ──────────────────────────────────────────────────────────────────────────────

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="tool_demo_agent",
    instruction="""
    あなたは計算と天気情報の取得ができるアシスタントです。

    以下のツールを使って質問に答えてください：
    - calculate: 計算式を評価します
    - get_weather: 都市の天気情報を取得します

    結果は日本語でわかりやすく伝えてください。
    """,
    # ↓↓↓ ここに 【穴埋め【2】】 の tools=[...] 引数を記述してください ↓↓↓
    tools=[
        FunctionTool(func=calculate),
        FunctionTool(func=get_weather),
    ],
)


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第2章：ツール付きエージェント")
    print("=" * 60)
    print()
    print("  使えるツール:")
    print("  📐 計算  - 例: 「1234 × 5678 を計算して」")
    print("  🌤️  天気  - 例: 「東京の天気は？」")
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
        app_name="basic_agent_app",
    )
    session = runner.runner.session_service.create_session_sync(
        app_name="basic_agent_app",
        user_id="student_001",
    )

    print("  ✅ エージェントの準備ができました！")
    print()

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
