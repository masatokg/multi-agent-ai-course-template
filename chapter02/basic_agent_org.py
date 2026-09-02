import warnings
warnings.filterwarnings("ignore")
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
    model="gemini-3.5-flash",
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

        print()


if __name__ == "__main__":
    main()
