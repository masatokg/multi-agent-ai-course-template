#Requires -Version 5.1
<#
.SYNOPSIS
    Google APIキー（代替キー・臨時キー）緊急切り替えスクリプト

.DESCRIPTION
    429エラー（レートリミット超過）発生時に、学生自身が別プロジェクトで作成した新キーに即座に差し替えます。
#>

param(
    [string]$NewApiKey = ""
)

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   🔑 Google APIキー 緊急切り替えツール" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if ([string]::IsNullOrWhiteSpace($NewApiKey)) {
    Write-Host "【429エラー（利用制限）が発生した場合の対処】" -ForegroundColor Yellow
    Write-Host "1. https://aistudio.google.com/ を開く" -ForegroundColor Yellow
    Write-Host "2. 「Create API key in new project」（新しいプロジェクトで作成）をクリック" -ForegroundColor Yellow
    Write-Host "3. 発行された新しいAPIキーをコピー" -ForegroundColor Yellow
    Write-Host ""
    $NewApiKey = Read-Host "新しい GOOGLE_API_KEY を入力"
    $NewApiKey = $NewApiKey.Trim()
}

if (-not ($NewApiKey.Length -gt 15 -and $NewApiKey -notmatch "\s")) {
    Write-Host "❌ APIキーの形式が正しくありません。（15文字以上かつ空白を含まないキーを入力してください）" -ForegroundColor Red
    exit 1
}

# 1. ユーザー環境変数を上書き
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", $NewApiKey, "User")
$env:GOOGLE_API_KEY = $NewApiKey

# 2. ローカル .env ファイルにも書き込み（即時反映用）
$envFile = Join-Path $SCRIPT_DIR ".env"
"GOOGLE_API_KEY=$NewApiKey" | Out-File -FilePath $envFile -Encoding utf8 -Force

Write-Host ""
Write-Host "✅ 代替APIキーを正常に設定しました！" -ForegroundColor Green
Write-Host "   - ユーザー環境変数: 更新完了" -ForegroundColor Green
Write-Host "   - ローカル .env ファイル: 作成/更新完了" -ForegroundColor Green
Write-Host ""
Write-Host "そのまま Python スクリプトを再実行してください。" -ForegroundColor White
Write-Host ""
