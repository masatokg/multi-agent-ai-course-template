import os
import sys
import time
import json
import warnings
import logging
from pathlib import Path

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
try:
    from google.adk.runners import InMemoryRunner as InProcessRunner
except ImportError:
    try:
        from google.adk.runners import Runner as InProcessRunner
    except ImportError:
        from google.adk.runners import InProcessRunner
from google.genai import types

load_dotenv(override=True)


os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
try:
    from google.adk.runners import InMemoryRunner as InProcessRunner
except ImportError:
    try:
        from google.adk.runners import Runner as InProcessRunner
    except ImportError:
        from google.adk.runners import InProcessRunner
from google.genai import types

load_dotenv(override=True)


os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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


os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



# ──────────────────────────────────────────────────────────────────────────────
# 簡易ナレッジベース（RAGのシミュレーション）
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】RAG（検索拡張生成）の実装方法
# │
# │【本ファイル（実行用）】
# │  KNOWLEDGE_BASE = {"ADK": "説明文", ...}  # 辞書でシミュレーション
# │  def search_knowledge(query: str) -> dict: ...   # 自作検索関数
# │
# │【教科書のサンプルコード（イメージ）】
# #  # 本格的なRAGはベクトルDBを使う例が多い
# #  import chromadb
# #  collection = chromadb.Client().create_collection("knowledge")
# #  collection.add(documents=[...], ids=[...])
# #  results = collection.query(query_texts=[query])
# │
# │【補足説明】
# │  本格的なRAGはベクトルデータベース（ChromaDB, Pinecone等）を使い、
# │  文章を数値ベクトルに変換して「意味的に近い文章」を検索します。
# │  本ファイルではその仕組みを理解するために、
# │  シンプルなキーワード検索でRAGの概念をシミュレーションしています。
# │  実際に試す場合は教科書のChromaDB等のコードを参照してください。
# └─────────────────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = {
    "ADK": "ADK（Agent Development Kit）は、Googleが開発したエージェント構築フレームワークです。LlmAgent、SequentialAgent、ParallelAgentなどの部品を組み合わせて使います。",
    "Gemini": "Geminiは、Googleが開発した大規模言語モデル（LLM）です。テキスト、画像、動画など多様な形式の入力を処理できます。",
    "RAG": "RAG（Retrieval-Augmented Generation）は、検索（Retrieval）と生成（Generation）を組み合わせた技術です。外部の知識をAIに参照させることで、最新情報や専用知識を活用できます。",
    "MCP": "MCP（Model Context Protocol）は、AIエージェントと外部ツールをつなぐ標準的な通信規約です。Anthropicが提唱し、GoogleやOpenAIなど多くの企業が採用しています。",
    "A2A": "A2A（Agent-to-Agent）は、エージェント同士が通信するためのプロトコルです。異なるフレームワークで作られたエージェントどうしでも連携できます。",
}


def search_knowledge(query: str) -> dict:
    """
    ナレッジベースを検索します（RAGの「検索」部分のシミュレーション）。

    Args:
        query: 検索クエリ

    Returns:
        検索結果を含む辞書
    """
    results = []
    query_lower = query.lower()

    for keyword, content in KNOWLEDGE_BASE.items():
        # キーワードがクエリに含まれているか確認
        if keyword.lower() in query_lower or query_lower in keyword.lower():
            results.append({"keyword": keyword, "content": content})

    if results:
        return {"status": "found", "results": results}
    else:
        return {
            "status": "not_found",
            "message": "ナレッジベースに該当情報がありませんでした",
        }


# ──────────────────────────────────────────────────────────────────────────────
# エージェントの定義（ナレッジベース検索ツール付き）
# ──────────────────────────────────────────────────────────────────────────────
from google.adk.tools import FunctionTool  # noqa: E402

root_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="memory_rag_agent",
    instruction="""
    あなたは「AIエージェント入門」コースの専属アシスタントです。

    質問を受けたら：
    1. まず search_knowledge ツールで社内ナレッジベースを検索する
    2. ナレッジベースに情報があれば、それを基に答える
    3. ナレッジベースに情報がなければ、一般的な知識で答える

    重要: 会話の流れを覚えており、前の質問との関連性を考慮して答えてください。
    例えば「それについてもっと詳しく」という質問には、直前の話題を参照してください。
    """,
    tools=[FunctionTool(func=search_knowledge)],
)


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第4章：Session・Memory・RAG デモ")
    print("=" * 60)
    print()
    print("  このエージェントは以下の用語についての知識を持っています：")
    for kw in KNOWLEDGE_BASE:
        print(f"  📚 {kw}")
    print()
    # ┌─────────────────────────────────────────────────────────────────────────
    # │【教科書との差分【2】】セッション（会話記憶）の仕組み
    # │
    # │【本ファイル（実行用）】
    # │  # 同じ session_id を使い続けることで会話履歴が自動的に保持される
    # │  session = runner.session_service.create_session_sync(app_name=..., user_id=...)
    # │  runner.run(session_id=session.id, ...)   # 毎回同じ session.id を渡す
    # │
    # │【教科書のサンプルコード（イメージ）】
    # #  # セッション管理が明示されていない簡略版の場合
    # #  agent.run(message, session_id="my_session")
    # │
    # │【補足説明】
    # │  ADK でのセッション管理のポイント：
    # │  - InMemorySessionService: セッションをメモリ上に保持（プログラム終了で消える）
    # │  - DatabaseSessionService: DBに保存（プログラム再起動後も記憶が残る）
    # │  教科書では DatabaseSessionService を使った永続的な記憶の例も
    # │  紹介されている場合があります。本ファイルは学習用途のため
    # │  シンプルな InMemorySessionService を使用しています。
    # └─────────────────────────────────────────────────────────────────────────
    print("  会話の流れを覚えているので、「それについてもっと詳しく」")
    print("  のような前の話題を参照する質問も試してみてください。")
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
        app_name="memory_agent_app",
    )
    session = runner.session_service.create_session_sync(
        app_name="memory_agent_app",
        user_id="student_001",
    )

    print("  ✅ エージェントの準備ができました！")
    print()

    turn_count = 0
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

        turn_count += 1
        print(f"  [会話 {turn_count}回目]")
        # エージェントに送信して返答を受け取る（503エラー自動3回リトライ＆切り替え機能付き）
        # エージェントに送信して返答を受け取る（503/429エラー自動対応機能付き）
        # エージェントに送信して返答を受け取る（503/429エラー自動対応＆スタックトレース非表示機能付き）
        # エージェントに送信して返答を受け取る（リアルタイム・ストリーミング出力 & 429/503エラー対応）
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

        print()


if __name__ == "__main__":
    main()