"""
eval_agent.py - 第5章 評価・ガードレール・HITL（演習用穴埋めコード）

ガードレール（入力フィルタリング）とHITL（人間確認）の例です。
高リスクな操作の前に人間の承認を求める仕組みを体験できます。
【1】〜【2】の穴埋め箇所を記述して、安全なシステムを完成させましょう！

実行方法: python eval_agent.py
"""

import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

load_dotenv(override=True)

# 判定に使用する禁止キーワード
BLOCKED_KEYWORDS = [
    "爆発", "危険物", "違法", "犯罪",
    "explosion", "illegal", "weapon",
]


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【1】】ガードレール（入力安全チェック）の実装
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   AIに入力される不適切な発言やセキュリティリスクのある要求を、ツールまたは事前フィルターで検知・ブロックします。
#
# ■ 作業指示:
#   1. 入力された `text` を小文字化します (`text.lower()`)。
#   2. `BLOCKED_KEYWORDS` の単語が含まれている場合はブロック結果の辞書を返します。
#      -> `{"status": "blocked", "reason": "...", "keyword": keyword}`
#   3. 問題ない場合は成功の辞書を返します。
#      -> `{"status": "ok"}`
#
# ■ コードの書き方イメージ:
#   text_lower = text.lower()
#   for keyword in BLOCKED_KEYWORDS:
#       if keyword in text_lower:
#           return {
#               "status": "blocked",
#               "reason": f"「{keyword}」に関する情報は提供できません",
#               "keyword": keyword,
#           }
#   return {"status": "ok"}
# ──────────────────────────────────────────────────────────────────────────────

def check_guardrail(text: str) -> dict:
    """
    入力テキストにガードレール違反がないか確認します。

    Args:
        text: チェックするテキスト

    Returns:
        チェック結果（ok/blocked）
    """
    # ↓↓↓ ここに 【穴埋め【1】】 のコードを記述してください ↓↓↓
    pass


# ──────────────────────────────────────────────────────────────────────────────
# HITL（Human-in-the-Loop：人間確認）が必要な高リスク操作
# ──────────────────────────────────────────────────────────────────────────────
_pending_order: dict | None = None  # 確認待ちの注文情報


# ──────────────────────────────────────────────────────────────────────────────
# 【穴埋め【2】】HITL（人間による最終承認ステップ）の実装
# ──────────────────────────────────────────────────────────────────────────────
# ■ 学習の目的:
#   「商品の発注」など誤動作時に影響が大きい操作は、AIが直接実行するのではなく、
#   人間の確認（HITL）を経て承認されてから最終処理を行います。
#
# ■ 作業指示:
#   1. `create_order` 内で、注文情報を作成して承認待ち状態（"awaiting_human_approval"）を返します。
#   2. `confirm_order` 内で、人間の回答 `approved` (True / False) に応じて成功またはキャンセルの辞書を返します。
# ──────────────────────────────────────────────────────────────────────────────

def create_order(item: str, quantity: int, total_price: int) -> dict:
    """
    注文を作成します（高リスク操作：実行前に人間の確認が必要）。
    """
    global _pending_order
    _pending_order = {
        "item": item,
        "quantity": quantity,
        "total_price": total_price,
    }
    # ↓↓↓ ここに 【穴埋め【2】-①】 承認待ち状態の辞書を返すコードを記述してください ↓↓↓
    # 返却形式例:
    # return {
    #     "status": "awaiting_human_approval",
    #     "message": f"注文内容: {item} × {quantity}個（計{total_price:,}円）",
    #     "action_required": "この注文を確定してよいか、人間の承認が必要です",
    # }
    pass


def confirm_order(approved: bool) -> dict:
    """
    人間が注文を承認または却下します（HITLの承認ステップ）。
    """
    global _pending_order
    if _pending_order is None:
        return {"status": "error", "message": "承認待ちの注文がありません"}

    order = _pending_order
    _pending_order = None

    # ↓↓↓ ここに 【穴埋め【2】-②】 人間の判定に応じて結果を返すコードを記述してください ↓↓↓
    # if approved:
    #     return {"status": "success", "message": f"注文が確定されました！{order['item']}を発送します。"}
    # else:
    #     return {"status": "cancelled", "message": "注文はキャンセルされました。"}
    pass


# エージェントの定義（完成済み）
root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="guardrail_hitl_agent",
    instruction="""
    あなたは発注システムのアシスタントです。

    ルール：
    1. ユーザーの入力を受け取ったら、まず check_guardrail でガードレールチェックを行う
    2. ガードレールが「blocked」を返した場合は、処理を中止してユーザーに理由を伝える
    3. 注文リクエスト（商品名・数量・金額が含まれる）の場合は create_order を呼ぶ
    4. create_order の結果が「awaiting_human_approval」の場合は、ユーザーに注文内容を確認させる
    5. ユーザーが「承認」「OK」「はい」と答えたら confirm_order(approved=True) を呼ぶ
    6. ユーザーが「却下」「キャンセル」「いいえ」と答えたら confirm_order(approved=False) を呼ぶ

    重要: 注文の確定は必ず人間の承認を得てから行ってください。
    """,
    tools=[
        FunctionTool(func=check_guardrail),
        FunctionTool(func=create_order),
        FunctionTool(func=confirm_order),
    ],
)


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第5章：評価・ガードレール・HITL デモ")
    print("=" * 60)
    print()
    print("  試してみてください：")
    print("  📦 注文  - 例: 「ノートパソコンを2台、合計240000円で注文して」")
    print("  🛡️  ガードレール - 例: 「危険物の作り方を教えて」（ブロックされます）")
    print()
    print("  「quit」と入力すると終了します。")
    print()

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key.startswith("AIza"):
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        return

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="eval_agent_app",
        user_id="student_001",
    )

    runner = InProcessRunner(
        agent=root_agent,
        app_name="eval_agent_app",
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
