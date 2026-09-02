"""
verify_setup.py - 環境構築確認スクリプト

このスクリプトを実行して、環境が正しく設定されているか確認します。
実行方法: python verify_setup.py
"""

import sys
import os

# Windowsコンソールでの文字化け・UnicodeEncodeError防止
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def check(label: str, ok: bool, detail: str = "") -> bool:
    icon = "[OK]" if ok else "[NG]"
    msg = f"  {icon}  {label}"
    if detail:
        msg += f": {detail}"
    print(msg)
    return ok


def main():
    print()
    print("=" * 56)
    print("  環境構築確認スクリプト")
    print("=" * 56)
    print()

    all_ok = True

    # ── Python バージョン確認 ─────────────────────────────────────────
    print("【Python】")
    major, minor = sys.version_info.major, sys.version_info.minor
    version_str = f"{major}.{minor}.{sys.version_info.micro}"
    ok = check(
        "Pythonバージョン",
        major >= 3 and minor >= 11,
        version_str + (" ✓" if major >= 3 and minor >= 11 else " → 3.11以上が必要"),
    )
    all_ok = all_ok and ok

    # ── 仮想環境確認 ──────────────────────────────────────────────────
    in_venv = sys.prefix != sys.base_prefix
    ok = check(
        "仮想環境(.venv)",
        in_venv,
        sys.prefix if in_venv else "有効化されていません",
    )
    all_ok = all_ok and ok
    print()

    # ── コアライブラリ確認 ────────────────────────────────────────────
    print("【ライブラリ】")

    # google-adk
    try:
        import google.adk as adk
        ver = getattr(adk, "__version__", "installed")
        ok = check("google-adk (ADK本体)", True, ver)
    except ImportError as e:
        ok = check("google-adk (ADK本体)", False, str(e))
    all_ok = all_ok and ok

    # google-generativeai
    try:
        import google.generativeai as genai
        ver = getattr(genai, "__version__", "installed")
        ok = check("google-generativeai (Gemini SDK)", True, ver)
    except ImportError as e:
        ok = check("google-generativeai (Gemini SDK)", False, str(e))
    all_ok = all_ok and ok

    # chromadb
    try:
        import chromadb
        ver = getattr(chromadb, "__version__", "installed")
        ok = check("chromadb (ベクトルDB)", True, ver)
    except ImportError as e:
        ok = check("chromadb (ベクトルDB)", False, str(e))
    all_ok = all_ok and ok

    # mcp
    try:
        import mcp
        ver = getattr(mcp, "__version__", "installed")
        ok = check("mcp (MCP Protocol)", True, ver)
    except ImportError as e:
        ok = check("mcp (MCP Protocol)", False, str(e))
    all_ok = all_ok and ok

    # a2a-sdk
    try:
        import a2a
        ver = getattr(a2a, "__version__", "installed")
        ok = check("a2a-sdk (A2A Protocol)", True, ver)
    except ImportError:
        try:
            import a2a_sdk
            ver = getattr(a2a_sdk, "__version__", "installed")
            ok = check("a2a-sdk (A2A Protocol)", True, ver)
        except ImportError as e:
            ok = check("a2a-sdk (A2A Protocol)", False, str(e))
    all_ok = all_ok and ok
    print()

    # ── APIキー確認 ───────────────────────────────────────────────────
    print("【APIキー】")
    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    has_key = bool(len(api_key) > 15)

    if has_key:
        masked = api_key[:8] + "..." + api_key[-4:]
        ok = check("GOOGLE_API_KEY", True, f"設定済み ({masked})")
    else:
        ok = check(
            "GOOGLE_API_KEY",
            False,
            "未設定または形式不正 → setup.ps1 を実行してキーを設定してください",
        )
    all_ok = all_ok and ok

    print()
    print("=" * 56)
    if all_ok:
        print("  🎉 環境構築チェック: すべてOKです！")
        print("     授業を始める準備が整いました。")
    else:
        print("  ❌ 一部の項目で問題が検出されました。")
        print("     上記のメッセージに従って設定を確認してください。")
    print("=" * 56)
    print()

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
