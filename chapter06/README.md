# 第6章：MCP & ツール統合

## 📖 この章で学ぶこと

- **MCP（Model Context Protocol）**: AIとツールをつなぐ「共通の言語」
- MCPサーバーの仕組みと使い方
- CLIツールをエージェントのツールとして使う方法

## 🗂️ ファイル説明

| ファイル | 内容 |
|---|---|
| `tool_agent.py` | MCPライクなツール統合のサンプル |

## 🚀 実行方法

```powershell
..\.venv\Scripts\Activate.ps1
python tool_agent.py
```

## 💡 ポイント解説

### MCPってなに？

MCP（Model Context Protocol）は、AIと外部ツールをつなぐための「共通の言語（規格）」です。

例えで言うと、**USBポート**のようなものです：
- パソコンにUSBポートがあれば、どのメーカーのUSBデバイスも接続できます
- MCPがあれば、どのAIエージェントでも、どのツールでも接続できます

### MCPがある世界とない世界

**MCPがない世界（N×M問題）：**
- 10個のAIアプリ × 20個のデータソース = 200個の接続コードが必要

**MCPがある世界（N+M問題）：**
- 10個のAIアプリ + 20個のデータソース = それぞれMCPに対応するだけ

これがMCPが普及した理由です。

### ADKでのMCPの使い方

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

mcp_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
    )
)
```
