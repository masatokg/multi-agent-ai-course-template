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
eval_agent.py - 第5章 評価・ガードレール・HITL

ガードレール（入力フィルタリング）とHITL（人間確認）の例です。
高リスクな操作の前に人間の承認を求める仕組みを体験できます。

実行方法: python eval_agent.py
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
    model="gemini-3.5-flash",
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
    if len(api_key) <= 15:
        print("  ❌ GOOGLE_API_KEY が設定されていません。")
        return

    # 💡 【重要：google-adk 2.8.0以降のセッション管理仕様】
    # 最新の google-adk では Runner（司令塔）が内部で専用の session_service を管理します。
    # `runner.session_service.create_session_sync(...)` からセッションを発行することで
# 会話履歴の不一致や Session not found エラーを防止します。
    runner = InProcessRunner(
        agent=root_agent,
        app_name="eval_agent_app",
    )
    session = runner.session_service.create_session_sync(
        app_name="eval_agent_app",
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
