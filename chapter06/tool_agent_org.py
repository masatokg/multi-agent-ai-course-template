"""
tool_agent.py - 第6章 MCP & ツール統合

MCPライクなツール統合の例です。
ファイル操作・コマンド実行・Webリクエストなど複数のツールを統合します。

注意: 実際のMCPはサーバーとの通信が必要ですが、
      このサンプルではMCPの概念を学ぶためにFunctionToolでシミュレーションします。

実行方法: python tool_agent.py
"""

import os
import json
import subprocess
from pathlib import Path
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】MCP の実装方法
# │
# │【本ファイル（実行用）】
# │  # MCP サーバーへの接続は行わず、FunctionTool で同等の機能をシミュレーション
# │  from google.adk.tools import FunctionTool
# │  def list_files(...): ...   # 自作関数でMCPツールを代替
# │
# │【教科書のサンプルコード（イメージ）】
# #  from google.adk.tools.mcp_tool import MCPToolset
# #  mcp_tools = MCPToolset.from_server(
# #      connection_params=StdioServerParameters(
# #          command="npx",
# #          args=["-y", "@modelcontextprotocol/server-filesystem", "."]
# #      )
# #  )
# │
# │【補足説明】
# │  本格的なMCPは専用のMCPサーバー（Node.js等で動く別プロセス）と
# │  通信して機能を呼び出します。本ファイルではMCPの概念を理解するため、
# │  MCPが提供するのと同等の機能（ファイル操作等）を Python 関数で
# │  シミュレーションしています。
# │  実際のMCPサーバーを使う場合は教科書の MCPToolset の例を参照してください。
# └─────────────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
try:
    from google.adk.runners import InMemoryRunner as InProcessRunner
except ImportError:
    try:
        from google.adk.runners import Runner as InProcessRunner
    except ImportError:
        from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv(override=True)


# ──────────────────────────────────────────────────────────────────────────────
# MCPツール群のシミュレーション
# 実際のMCPサーバーが提供するツールに相当します
# ──────────────────────────────────────────────────────────────────────────────

def list_files(directory: str = ".") -> dict:
    """
    指定ディレクトリのファイル一覧を取得します（MCPファイルシステムツールのシミュレーション）。

    Args:
        directory: 一覧表示するディレクトリパス（デフォルト: カレントディレクトリ）

    Returns:
        ファイル一覧
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
    except PermissionError:
        return {"status": "error", "message": "アクセス権限がありません"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def read_file(filepath: str) -> dict:
    """
    テキストファイルの内容を読み取ります。

    Args:
        filepath: 読み取るファイルのパス

    Returns:
        ファイル内容
    """
    try:
        path = Path(filepath)
        if not path.exists():
            return {"status": "error", "message": f"ファイルが見つかりません: {filepath}"}
        if not path.is_file():
            return {"status": "error", "message": f"ファイルではありません: {filepath}"}

        content = path.read_text(encoding="utf-8", errors="replace")
        # 長すぎる場合は最初の2000文字のみ
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


def run_python_code(code: str) -> dict:
    """
    Pythonコードを安全に実行します（CLIツール統合のシミュレーション）。
    ※ 安全のため、基本的な演算のみ許可します。

    Args:
        code: 実行するPythonコード（1行の式のみ）

    Returns:
        実行結果
    """
    # 安全チェック：危険なキーワードをブロック
    dangerous = ["import os", "import sys", "open(", "exec(", "eval(", "__import__",
                 "subprocess", "shutil", "rmdir", "remove", "unlink"]
    for d in dangerous:
        if d in code:
            return {
                "status": "blocked",
                "message": f"安全のため「{d}」を含むコードは実行できません",
            }

    try:
        # 数式・リスト操作など基本的な処理のみ許可
        allowed_builtins = {
            "abs": abs, "round": round, "len": len, "sum": sum,
            "min": min, "max": max, "sorted": sorted, "list": list,
            "dict": dict, "set": set, "tuple": tuple, "range": range,
            "str": str, "int": int, "float": float, "bool": bool,
            "print": print, "type": type,
        }
        result = eval(code, {"__builtins__": allowed_builtins})  # noqa: S307
        return {"status": "success", "code": code, "result": result}
    except Exception as e:
        return {"status": "error", "code": code, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# エージェントの定義（複数ツールを統合）
# ──────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    model="gemini-3.6-flash",
    name="mcp_simulated_agent",
    instruction="""
    あなたはファイル操作とコード実行ができるアシスタントです。

    使えるツール：
    - list_files: ディレクトリのファイル一覧を表示
    - read_file: テキストファイルの内容を読み取る
    - run_python_code: Pythonの式や計算を実行する

    MCPのツールセットとして、これらのツールを組み合わせて
    ユーザーの要求に答えてください。

    ファイルパスについては、相対パスを使う場合はカレントディレクトリ
    からの相対パスで指定してください。
    """,
    tools=[
        FunctionTool(func=list_files),
        FunctionTool(func=read_file),
        FunctionTool(func=run_python_code),
    ],
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

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="tool_agent_app",
        user_id="student_001",
    )

    runner = InProcessRunner(
        agent=root_agent,
        app_name="tool_agent_app",
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
