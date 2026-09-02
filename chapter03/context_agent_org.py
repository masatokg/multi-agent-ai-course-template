import os
import sys
import warnings
import logging

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



# ──────────────────────────────────────────────────────────────────────────────
# サブエージェント【1】：調査担当
# プロンプト（instruction）を具体的に書くことで、役割が明確になります
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【1】】サブエージェントの定義方法
# │
# │【本ファイル（実行用）】
# │  research_agent = LlmAgent(
# │      model="gemini-3.5-flash",
# │      name="research_agent",
# │      description="...",   ← sub_agentsで使う場合は description が重要
# │      instruction="...",
# │  )
# │
# │【教科書のサンプルコード（イメージ）】
# #  research_agent = Agent(
# #      name="research_agent",
# #      instruction="...",
# #  )
# │
# │【補足説明】
# │  サブエージェントを親エージェント（orchestrator）の sub_agents に
# │  登録する場合、"description" 引数が重要です。
# │  親エージェントは description を読んで「このエージェントに何を頼むべきか」
# │  を判断します。教科書では省略されている場合がありますが、
# │  実際の動作の安定性のために追加しています。
# └─────────────────────────────────────────────────────────────────────────────
research_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="research_agent",
    instruction="""
    あなたはリサーチ専門のエージェントです。

    ユーザーからテーマを受け取ったら、以下の構造でリサーチ結果をまとめてください：

    ## テーマ概要
    （テーマを1〜2文で説明）

    ## 主要なポイント（3つ）
    1. （ポイント1）
    あなたは最新テクノロジーの調査専門のエージェントです。
    ユーザーからテーマを受け取ったら、重要なキーポイントを3〜5個にまとめて抽出してください。
    回答は箇条書きで、事実のみを簡潔に記述してください。
    """,
)


# ──────────────────────────────────────────────────────────────────────────────
# サブエージェント【2】：執筆担当
# ──────────────────────────────────────────────────────────────────────────────
writer_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="writer_agent",
    instruction="""
    あなたはわかりやすい文章を書く専門のエージェントです。

    調査結果を受け取ったら、高校生でも理解できるような文章に変換してください。

    ルール：
    - 専門用語には必ず説明を加える（例：「〇〇（専門用語の説明）」）
    - 箇条書きよりも自然な文章を使う
    - 具体的な例えを1つ以上含める
    - 全体を400字程度にまとめる
    """,
)


# ──────────────────────────────────────────────────────────────────────────────
# オーケストレーター（指揮者エージェント）
# サブエージェントを組み合わせて、タスクを分担させます
# ──────────────────────────────────────────────────────────────────────────────
# ┌─────────────────────────────────────────────────────────────────────────────
# │【教科書との差分【2】】sub_agents によるマルチエージェント構成
# │
# │【本ファイル（実行用）】
# │  root_agent = LlmAgent(
# │      ...
# │      sub_agents=[research_agent, writer_agent],
# │  )
# │
# │【教科書のサンプルコード（イメージ）】
# #  # SequentialAgent を使う例（教科書によって異なる）
# #  from google.adk.agents import SequentialAgent
# #  pipeline = SequentialAgent(
# #      sub_agents=[research_agent, writer_agent]
# #  )
# │
# │【補足説明】
# │  教科書では SequentialAgent（順番に実行）や ParallelAgent（並列実行）を
# │  使った例が紹介されている場合があります。
# │  本ファイルでは LlmAgent の sub_agents に渡す方法を採用しています。
# │  この方法では、親エージェントが自分でサブエージェントの実行順を判断します
# │  （より柔軟ですが、SequentialAgent より動作が「AIの判断依存」になります）。
# └─────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    model="gemini-3.5-flash",
    name="orchestrator_agent",
    instruction="""
    あなたはレポート作成チームのリーダーです。

    ユーザーからテーマを受け取ったら：
    1. research_agent（調査担当）に詳細なリサーチを依頼する
    2. その結果を writer_agent（執筆担当）に渡し、わかりやすい文章に変換させる
    3. 完成したレポートをユーザーに提示する

    チーム全体の品質に責任を持ってください。
    """,
    sub_agents=[research_agent, writer_agent],
)


# ──────────────────────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  🤖 第3章：Context Engineering & Agent Skills")
    print("=" * 60)
    print()
    print("  このデモでは、2つのエージェントが協力してレポートを作ります：")
    print("  📚 調査担当エージェント → テーマをリサーチ")
    print("  ✍️  執筆担当エージェント → わかりやすく文章化")
    print()
    print("  テーマを入力してください（例: 「機械学習とは」「量子コンピュータ」）")
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
        app_name="context_agent_app",
    )
    session = runner.session_service.create_session_sync(
        app_name="context_agent_app",
        user_id="student_001",
    )

    print("  ✅ エージェントチームの準備ができました！")
    print()

    while True:
        try:
            user_input = input("テーマ> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.lower() in ("quit", "exit", "終了"):
            print("  👋 終了します。お疲れさまでした！")
            break

        if not user_input:
            continue

        print()
        print("  📝 レポートを作成中です（少々お待ちください）...")
        print()

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


if __name__ == "__main__":
    main()
