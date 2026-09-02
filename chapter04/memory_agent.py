"""
memory_agent.py - 第4章 Session・Memory・RAG（演習用穴埋めコード）

会話履歴を記憶するエージェントと、簡易RAGの例です。
前の会話を覚えており、過去に話した内容を参照して答えます。
【1】〜【2】の穴埋め箇所を記述して、記憶・検索エージェントを完成させましょう！

実行方法: python memory_agent.py
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
# 簡易ナレッジベース（RAGのシミュレーション）
# ──────────────────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = {
    "ADK": "ADK（Agent Development Kit）は、Googleが開発したエージェント構築フレームワークです。LlmAgent、SequentialAgent、ParallelAgentなどの部品を組み合わせて使います。",
    "Gemini": "Geminiは、Googleが開発した大規模言語モデル（LLM）です。テキスト、画像、動画など多様な形式の入力を処理できます。",
    "RAG": "RAG（Retrieval-Augmented Generation）は、検索（Retrieval）と生成（Generation）を組み合わせた技術です。外部の知識をAIに参照させることで、最新情報や専用知識を活用できます。",
    "MCP": "MCP（Model Context Protocol）は、AIエージェントと外部ツールをつなぐ標準的な通信規約です。Anthropicが提唱し、GoogleやOpenAIなど多くの企業が採用しています。",
    "A2A": "A2A（Agent-to-Agent）は、エージェント同士が通信するためのプロトコルです。異なるフレームワークで作られたエージェントどうしでも連携できます。",
}


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【1】】RAGの「検索（Retrieval）」ツールの実装
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   RAG（検索拡張生成）のコアである「ナレッジベースからの検索ロジック」を記述します。
#   ユーザーのクエリキーワードに合致する情報を辞書から抽出し、AIが回答に使える形で返します。
#
# ■ 作業指示:
#   1. `query_lower = query.lower()` で小文字化し、大文字小文字の違いを吸収します。
#   2. `KNOWLEDGE_BASE` 内の各 `keyword` に対し、クエリに含まれるか判定します。
#   3. 発見された場合: `return {"status": "found", "results": results}` を返します。
#   4. 見つからない場合: `return {"status": "not_found", "message": "..."}` を返します。
#
# ■ コードの書き方イメージ:
#   results = []
#   for keyword, content in KNOWLEDGE_BASE.items():
#       if keyword.lower() in query.lower():
#           results.append({"keyword": keyword, "content": content})
#   if results:
#       return {"status": "found", "results": results}
#   return {"status": "not_found", "message": "該当情報がありません"}
# ──────────────────────────────────────────────────────────────────────────────

def search_knowledge(query: str) -> dict:
    """
    ナレッジベースを検索します（RAGの「検索」部分のシミュレーション）。

    Args:
        query: 検索クエリ

    Returns:
        検索結果を含む辞書
    """
    # ↓↓↓ ここに 【穴埋め【1】】 のコードを記述してください ↓↓↓
    results = []
    for keyword, content in KNOWLEDGE_BASE.items():
        if keyword.lower() in query.lower():
            results.append({"keyword": keyword, "content": content})
    if results:
        return {"status": "found", "results": results}
    return {"status": "not_found", "message": "該当情報がありません"}


# エージェントの定義（完成済み）
root_agent = LlmAgent(
    model="gemini-3.6-flash",
    name="memory_rag_agent",
    instruction="""
    あなたは「AIエージェント入門」コースの専属アシスタントです。

    質問を受けたら：
    1. まず search_knowledge ツールで社内ナレッジベースを検索する
    2. ナレッジベースに情報があれば、それを基に答える
    3. ナレッジベースに情報がなければ、一般的な知識で答える

    重要: 会話の流れを覚えており、前の質問との関連性を考慮して答えてください。
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
    print("  会話の流れを覚えているので、「それについてもっと詳しく」")
    print("  のような前の話題を参照する質問も試してみてください。")
    print()
    print("  「quit」と入力すると終了します。")
    print()

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if len(api_key) <= 15:
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        return

    
    # ──────────────────────────────────────────────────────────────────────────
    # 【穴埋め【2】】会話コンテキスト（記憶）を維持するセッション作成
    # ──────────────────────────────────────────────────────────────────────────
    # ■ 学習の目的:
    #   毎回の対話で同一の `session_id` を使い続けることで、AIに過去の会話履歴（文脈）を保持させます。
    #
    # ■ 作業指示:
    #   `runner.session_service.create_session_sync(...)` を呼び出して `session` 変数に保存してください。
    #   - app_name: "memory_agent_app"
    #   - user_id: "student_001"
    #
    # ■ 記述例:
    #   # 💡 ポイント (google-adk 2.8.0+): runner 内部の session_service からセッションを発行します
    #   session = runner.session_service.create_session_sync(
    #       app_name="memory_agent_app",
    #       user_id="student_001",
    #   )
    # ──────────────────────────────────────────────────────────────────────────

    # ↓↓↓ ここに 【穴埋め【2】】 のコードを記述してください ↓↓↓
    session = None  # ← create_session(...) の戻り値を代入してください

    # 💡 【重要：google-adk 2.8.0以降のセッション管理仕様】
    # 最新の google-adk では Runner（司令塔）が内部で専用の session_service を管理します。
    # `runner.session_service.create_session_sync(...)` からセッションを発行することで
# 会話履歴の不一致や Session not found エラーを防止します。
    runner = InProcessRunner(
        agent=root_agent,
        app_name="memory_agent_app",
        
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
                session_id=session.id if session else "",
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
