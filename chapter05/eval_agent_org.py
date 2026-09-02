"""
eval_agent.py - 第5章 評価・ガードレール・HITL

ガードレール（入力フィルタリング）とHITL（人間確認）の例です。
高リスクな操作の前に人間の承認を求める仕組みを体験できます。

実行方法: python eval_agent.py
"""

import os
from google.adk.agents import LlmAgent
from google.adk.runners import InProcessRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types


# ──────────────────────────────────────────────────────────────────────────────
# ガードレール：禁止ワードチェック
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】ガードレールの実装方法
# │
# │【本ファイル（実行用）】
# │  # ガードレールをツール（FunctionTool）として実装し、
# │  # エージェント自身が instruction に従って判断・呼び出す
# │  def check_guardrail(text: str) -> dict: ...
# │  root_agent = LlmAgent(tools=[FunctionTool(func=check_guardrail), ...])
# │
# │【教科書のサンプルコード（イメージ）】
# #  # before_call_hook や callback を使う例
# #  from google.adk.callbacks import before_call
# #  @before_call
# #  def guardrail_hook(context):
# #      if "危険" in context.message:
# #          raise GuardrailError("ブロックされました")
# │
# │【補足説明】
# │  ガードレールの実装方法は大きく2種類あります：
# │  【1】 フック/コールバック方式: エージェントの実行前後に自動で呼ばれる
# │    （教科書で紹介される場合あり・より本格的）
# │  【2】 ツール方式: エージェントがinstructionに従って自分でツールを呼ぶ
# │    （本ファイルの方法・シンプルで理解しやすい）
# │  本ファイルはガードレールの「概念」を学ぶためのシンプルな実装です。
# └─────────────────────────────────────────────────────────────────────────────
BLOCKED_KEYWORDS = [
    "爆発", "危険物", "違法", "犯罪",
    "explosion", "illegal", "weapon",
]


def check_guardrail(text: str) -> dict:
    """
    入力テキストにガードレール違反がないか確認します。

    Args:
        text: チェックするテキスト

    Returns:
        チェック結果（ok/blocked）
    """
    text_lower = text.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in text_lower:
            return {
                "status": "blocked",
                "reason": f"「{keyword}」に関する情報は提供できません",
                "keyword": keyword,
            }
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# HITL（人間確認）が必要な高リスク操作のシミュレーション
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【2】】HITL（Human-in-the-Loop）の実装方法
# │
# │【本ファイル（実行用）】
# │  # create_order → "awaiting_human_approval" を返す
# │  # → AIがユーザーに確認を求める
# │  # → ユーザーの返答に応じて confirm_order を呼ぶ
# │  # （会話の流れでHITLを実現）
# │
# │【教科書のサンプルコード（イメージ）】
# #  # interrupt/resume 機能を使う例（より本格的なHITL）
# #  runner.interrupt()   # エージェントを一時停止
# #  # 人間が確認...
# #  runner.resume(approved=True)  # 承認して再開
# │
# │【補足説明】
# │  本格的な HITL は ADK の interrupt/resume 機能や
# │  Workflow のチェックポイント機能を使います。
# │  本ファイルでは「会話の中でユーザーに確認を取る」という
# │  シンプルな方法でHITLの概念を実演しています。
# │  実際のシステムではUI画面に「承認ボタン」を表示する等の
# │  実装が必要になります。
# └─────────────────────────────────────────────────────────────────────────────

_pending_order: dict | None = None  # 確認待ちの注文情報


def create_order(item: str, quantity: int, total_price: int) -> dict:
    """
    注文を作成します（高リスク操作：実行前に人間の確認が必要）。

    Args:
        item: 商品名
        quantity: 数量
        total_price: 合計金額（円）

    Returns:
        HITL確認リクエスト
    """
    global _pending_order
    _pending_order = {
        "item": item,
        "quantity": quantity,
        "total_price": total_price,
    }
    return {
        "status": "awaiting_human_approval",
        "message": f"注文内容: {item} × {quantity}個（計{total_price:,}円）",
        "action_required": "この注文を確定してよいか、人間の承認が必要です",
        "order_id": "ORD-2024-001",
    }


def confirm_order(approved: bool) -> dict:
    """
    人間が注文を承認または却下します（HITLの承認ステップ）。

    Args:
        approved: True=承認, False=却下

    Returns:
        処理結果
    """
    global _pending_order
    if _pending_order is None:
        return {"status": "error", "message": "承認待ちの注文がありません"}

    order = _pending_order
    _pending_order = None

    if approved:
        return {
            "status": "success",
            "message": f"注文が確定されました！{order['item']} × {order['quantity']}個 を発注しました。",
            "order_id": "ORD-2024-001",
        }
    else:
        return {
            "status": "cancelled",
            "message": "注文はキャンセルされました。",
        }


# ──────────────────────────────────────────────────────────────────────────────
# エージェントの定義
# ──────────────────────────────────────────────────────────────────────────────
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
