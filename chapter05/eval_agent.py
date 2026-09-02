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
eval_agent.py - 第5章 評価・ガードレール・HITL（演習用穴埋めコード）

ガードレール（入力フィルタリング）とHITL（人間確認）の例です。
高リスクな操作の前に人間の承認を求める仕組みを体験できます。
【1】〜【2】の穴埋め箇所を記述して、安全なシステムを完成させましょう！

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
    if approved:
        return {"status": "success", "message": f"注文が確定されました！{order['item']}を発送します。"}
    else:
        return {"status": "cancelled", "message": "注文はキャンセルされました。"}


# エージェントの定義（完成済み）
root_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="evaluated_agent",
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
        # エージェントに送信して返答を受け取る（503/429エラー自動対応＆スタックトレース非表示機能付き）
        success = False
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print("AI> ", end="", flush=True)
                
                # ADK内部の生のTraceback出力を一時遮断
                import io, sys, contextlib
                stderr_buffer = io.StringIO()
                with contextlib.redirect_stderr(stderr_buffer):
                    events = list(runner.run(
                        user_id="student_001",
                        session_id=session.id,
                        new_message=types.Content(
                            role="user",
                            parts=[types.Part(text=user_input)],
                        ),
                    ))
                
                for event in events:
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
