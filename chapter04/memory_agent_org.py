"""
memory_agent.py - 第4章 Session・Memory・RAG

会話履歴を記憶するエージェントと、簡易RAGの例です。
前の会話を覚えており、過去に話した内容を参照して答えます。

実行方法: python memory_agent.py
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv(override=True)


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
    model="gemini-2.0-flash",
    name="memory_agent",
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
    # │  session = session_service.create_session(app_name=..., user_id=...)
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
    if not api_key.startswith("AIza"):
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        return

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="memory_agent_app",
        user_id="student_001",
    )

    runner = InProcessRunner(
        agent=root_agent,
        app_name="memory_agent_app",
        session_service=session_service,
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
