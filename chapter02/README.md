# 第2章：ADK エージェント開発フレームワーク

## 📖 この章で学ぶこと

- ADKのアーキテクチャ（設計思想）
- LlmAgent（AIが思考するエージェント）の使い方
- FunctionTool（エージェントが使えるツール）の作り方
- エージェントに「計算機」ツールを持たせる

## 🗂️ ファイル説明

| ファイル | 内容 |
|---|---|
| `basic_agent.py` | ツール付きエージェントのサンプル |

## 🚀 実行方法

```powershell
# 仮想環境を有効にする（まだしていない場合）
..\.venv\Scripts\Activate.ps1

# サンプルを実行
python basic_agent.py
```

## 💡 ポイント解説

### ツール（Tool）ってなに？

エージェントが「使える道具」のことです。

例えば：
- 🔢 **計算ツール** → 「100 × 3 ÷ 2 は？」と聞くと計算してくれる
- 🌐 **ウェブ検索ツール** → 「今日のニュースは？」と聞くと検索してくれる
- 📁 **ファイル読み取りツール** → 「このCSVファイルを分析して」と頼める

ツールがあることで、エージェントはAIの「頭脳」だけでなく、外の世界と連携できるようになります。

### FunctionTool の書き方

Pythonの関数に `@tool` デコレータをつけるだけでツールになります。

```python
from google.adk.tools import FunctionTool

def calculate(expression: str) -> str:
    """計算式を評価します"""
    return str(eval(expression))

calc_tool = FunctionTool(func=calculate)
```
