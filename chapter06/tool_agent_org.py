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
    model="gemini-3.5-flash",
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

    # 💡 【重要：google-adk 2.8.0以降のセッション管理仕様】
    # 最新の google-adk では Runner（司令塔）が内部で専用の session_service を管理します。
    # `runner.session_service.create_session_sync(...)` からセッションを発行することで
# 会話履歴の不一致や Session not found エラーを防止します。
    runner = InProcessRunner(
        agent=root_agent,
        app_name="tool_agent_app",
    )
    session = runner.session_service.create_session_sync(
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

        # エージェントに送信して返答を受け取る（503エラー自動3回リトライ＆切り替え機能付き）
        # エージェントに送信して返答を受け取る（503/429エラー自動対応機能付き）
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
                        # そのままループで再試行
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

        print()


if __name__ == "__main__":
    main()
