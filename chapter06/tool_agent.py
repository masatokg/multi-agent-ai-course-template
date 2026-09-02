"""
tool_agent.py - 第6章 MCP & ツール統合（演習用穴埋めコード）

MCPライクなツール統合の例です。
ファイル操作・コード実行など複数のツールを統合します。
【1】〜【2】の穴埋め箇所を記述して、万能なツール連携エージェントを完成させましょう！

実行方法: python tool_agent.py
"""

import os
import json
import subprocess
from pathlib import Path
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
# MCPツール群のシミュレーション（ファイル一覧・閲覧）
# ──────────────────────────────────────────────────────────────────────────────

def list_files(directory: str = ".") -> dict:
    """
    指定ディレクトリのファイル一覧を取得します。
    """
    try:
        path = Path(directory)
        if not path.exists():
            return {"status": "error", "message": f"ディレクトリが見つかりません: {directory}"}

        items = []
        for item in sorted(path.iterdir()):
            item_type = "📁 フォルダ" if item.is_dir() else "📄 ファイル"
            size = "" if item.is_dir() else f"({item.stat().st_size:,} bytes)"
            items.append(f"{item_type}: {item.name} {size}")

        return {
            "status": "success",
            "directory": str(path.absolute()),
            "count": len(items),
            "items": items,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def read_file(filepath: str) -> dict:
    """
    テキストファイルの内容を読み取ります。
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return {"status": "error", "message": f"ファイルが見つかりません: {filepath}"}

        content = path.read_text(encoding="utf-8", errors="replace")
        if len(content) > 2000:
            content = content[:2000] + "\n... (省略)"

        return {
            "status": "success",
            "filepath": str(path.absolute()),
            "size": path.stat().st_size,
            "content": content,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【1】】安全なコード実行ツールの実装
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   MCP（Model Context Protocol）などで提供される「コード実行機能」を安全に提供するため、
#   危険な構文や組み込み関数を制限（サンドボックス化）した実行ツールを作成します。
#
# ■ 作業指示:
#   1. `dangerous` リスト（"import os", "eval", "open" など）の文字列が `code` に含まれる場合、
#      `{"status": "blocked", "message": "..."}` を返します。
#   2. 安全な組み込み関数のみを許可した `allowed_builtins` を使って `eval(code, {"__builtins__": allowed_builtins})` を実行します。
#   3. 成功時は `{"status": "success", "code": code, "result": result}` を返します。
#
# ■ コードの書き方イメージ:
#   dangerous = ["import os", "open(", "eval(", "exec("]
#   for d in dangerous:
#       if d in code:
#           return {"status": "blocked", "message": f"「{d}」を含むコードはブロックされました"}
#   try:
#       allowed_builtins = {"abs": abs, "len": len, "sum": sum, "print": print}
#       result = eval(code, {"__builtins__": allowed_builtins})
#       return {"status": "success", "code": code, "result": result}
#   except Exception as e:
#       return {"status": "error", "error": str(e)}
# ──────────────────────────────────────────────────────────────────────────────

def run_python_code(code: str) -> dict:
    """
    Pythonコードを安全に実行します（CLIツール統合のシミュレーション）。
    """
    # ↓↓↓ ここに 【穴埋め【1】】 のコードを記述してください ↓↓↓
    pass


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【2】】複数ツールを保持するマルチツールエージェントの作成
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   MCPや外部システムで提供される複数の機能（ファイル一覧、ファイル閲覧、コード実行）を
#   エージェントの `tools` に一括で登録し、要求に応じて適切なツールを選択させます。
#
# ■ 作業指示:
#   `tools` 引数に `FunctionTool(func=list_files)`, `FunctionTool(func=read_file)`, `FunctionTool(func=run_python_code)`
#   の3つをリスト形式で設定してください。
# ──────────────────────────────────────────────────────────────────────────────

root_agent = LlmAgent(
    model="gemini-3.6-flash",
    name="mcp_tool_agent",
    instruction="""
    あなたはファイル操作とコード実行ができるアシスタントです。

    使えるツール：
    - list_files: ディレクトリのファイル一覧を表示
    - read_file: テキストファイルの内容を読み取る
    - run_python_code: Pythonの式や計算を実行する

    MCPのツールセットとして、これらのツールを組み合わせて
    ユーザーの要求に答えてください。
    """,
    # ↓↓↓ ここに 【穴埋め【2】】 の tools=[...] 引数を記述してください ↓↓↓
)


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第6章：MCP & ツール統合 デモ")
    print("=" * 60)
    print()
    print("  使えるツール（MCPシミュレーション）：")
    print("  📁 ファイル一覧  - 例: 「このフォルダのファイルを見せて」")
    print("  📄 ファイル読取  - 例: 「README.mdを読んで要約して」")
    print("  🐍 Python実行   - 例: 「2の10乗を計算して」")
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
        app_name="tool_agent_app",
    )
    session = runner.runner.session_service.create_session_sync(
        app_name="tool_agent_app",
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
