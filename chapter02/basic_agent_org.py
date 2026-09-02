"""
basic_agent.py - 第2章 ツール付きエージェント

エージェントに「計算ツール」と「天気取得ツール（ダミー）」を持たせた例です。
ツール（Tool）を使うことで、エージェントの能力を拡張できます。

実行方法: python basic_agent.py
"""

import os
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】インポート：FunctionTool の使い方
# │
# │【本ファイル（実行用）】
# │  from google.adk.tools import FunctionTool
# │  # Python 関数を FunctionTool でラップしてエージェントに渡す
# │
# │【教科書のサンプルコード（イメージ）】
# #  from google.adk.tools import tool   # デコレータ形式の場合
# #  @tool
# #  def calculate(expression: str) -> dict: ...
# │
# │【補足説明】
# │  ADK でツールを定義する方法は主に2種類あります：
# │  【1】 FunctionTool(func=関数) でラップする方法（本ファイルの方法）
# │  【2】 @tool デコレータを関数に付ける方法（教科書で紹介される場合あり）
# │  どちらも動作は同じで、AIがツールを「使える道具」として認識します。
# └─────────────────────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv(override=True)


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
    # ┌─────────────────────────────────────────────────────────────────────────
    # │【教科書との差分【2】】ツール関数の戻り値の形式
    # │
    # │【本ファイル（実行用）】
    # │  return {"status": "success", "expression": expression, "result": result}
    # │  # → 辞書（dict）形式で返す
    # │
    # │【教科書のサンプルコード（イメージ）】
    # #  return result   # 値をそのまま返す例
    # │
    # │【補足説明】
    # │  ADK のツール関数は辞書（dict）形式で返すことが推奨されています。
    # │  理由：AIがツールの結果を解釈しやすくなるためです。
    # │  "status" キーを含めると、成功/失敗の判定がしやすくなります。
    # └─────────────────────────────────────────────────────────────────────────
    try:
        # ※実際の本番環境では eval() の使用は避け、専用の計算ライブラリを使います
        result = eval(expression)  # noqa: S307
        return {"status": "success", "expression": expression, "result": result}
    except Exception as e:
        return {"status": "error", "expression": expression, "error": str(e)}


def get_weather(city: str) -> dict:
    """
    指定した都市の天気を取得します（デモ用ダミーデータ）。

    Args:
        city: 都市名（例: "Tokyo", "Osaka"）

    Returns:
        天気情報を含む辞書
    """
    # 注意: これはデモ用のダミーデータです
    weather_data = {
        "Tokyo": {"temperature": 28, "condition": "晴れ", "humidity": 65},
        "Osaka": {"temperature": 30, "condition": "曇り", "humidity": 70},
        "Fukuoka": {"temperature": 32, "condition": "雨", "humidity": 85},
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
# エージェントの定義（ツールを持たせる）
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【3】】ツールの登録方法
# │
# │【本ファイル（実行用）】
# │  root_agent = LlmAgent(
# │      ...
# │      tools=[
# │          FunctionTool(func=calculate),
# │          FunctionTool(func=get_weather),
# │      ],
# │  )
# │
# │【教科書のサンプルコード（イメージ）】
# #  agent = Agent(
# #      ...
# #      tools=[calculate, get_weather],   # 関数を直接渡す例
# #  )
# │
# │【補足説明】
# │  教科書では関数を直接 tools=[] に渡す例が示されている場合があります。
# │  ADK の正式な方法は FunctionTool(func=関数) でラップして渡します。
# │  どちらも動作は似ていますが、FunctionTool を使うと
# │  ツールの説明文（docstring）が自動的にAIに伝わり、
# │  AIがより適切にツールを選択できるようになります。
# └─────────────────────────────────────────────────────────────────────────────
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
    if not api_key.startswith("AIza"):
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        return

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="basic_agent_app",
        user_id="student_001",
    )

    runner = InProcessRunner(
        agent=root_agent,
        app_name="basic_agent_app",
        session_service=session_service,
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
