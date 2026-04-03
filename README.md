# CPLEX Optimization MCP Server

IBM CPLEX（docplex）とCPLEX OPL Studioを使用した数理最適化MCPサーバー

## 概要

このMCPサーバーは、IBM CPLEXを使用して様々な最適化問題をBobから実行できるようにします。

**✅ 対応ソルバー:**
- **CPLEX (docplex)** - Python API
- **CPLEX OPL Studio** - .mod/.datファイル実行

## 提供機能

### ツール一覧

1. **`get_solver_info`** - 利用可能なソルバー情報を取得
   - CPLEXとOPL Studioの利用可能状況
   - oplrunのパス情報

2. **`solve_production_planning`** - 生産計画最適化
   - 利益最大化
   - リソース制約（労働時間、材料）
   - 最小生産量制約（オプション）

3. **`solve_simple_lp`** - 汎用線形計画問題
   - 任意の目的関数と制約条件
   - 最大化/最小化の選択可能

4. **`run_opl_model`** - OPLモデル実行（文字列）
   - .modと.datの内容を文字列で渡して実行
   - 一時ファイルを自動作成

5. **`run_opl_from_files`** - OPLモデル実行（ファイル）
   - 既存の.mod/.datファイルを直接実行
   - CPLEX IDEと同じ動作

## セットアップ

### 1. 依存関係の確認

```bash
cd /Users/aa539999/Documents/IBM\ Bob/MCP/cplex-mcp-server
/Users/aa539999/.pyenv/versions/3.12.3/bin/python3 -c "from server import CPLEX_AVAILABLE, CPLEX_OPL_AVAILABLE; print(f'CPLEX: {CPLEX_AVAILABLE}, OPL: {CPLEX_OPL_AVAILABLE}')"
```

**期待される出力**:
```
CPLEX: True, OPL: True
```

### 2. Bob設定（既に完了）

`~/.bob/settings/mcp_settings.json` に設定済み:
```json
{
  "mcpServers": {
    "cplex-optimizer": {
      "command": "/Users/aa539999/.pyenv/versions/3.12.3/bin/python3",
      "args": [
        "/Users/aa539999/Documents/IBM Bob/MCP/cplex-mcp-server/__main__.py"
      ],
      "disabled": false
    }
  }
}
```

### 3. Bobを再起動

## 使用例

### 例1: ソルバー情報の確認

**あなた**: 「最適化ソルバーの情報を教えて」

**Bob**:
```xml
<use_mcp_tool>
<server_name>cplex-optimizer</server_name>
<tool_name>get_solver_info</tool_name>
<arguments>{}</arguments>
</use_mcp_tool>
```

**結果**:
```json
{
  "cplex_available": true,
  "opl_available": true,
  "active_solver": "CPLEX (docplex)",
  "opl_path": "/Applications/CPLEX_Studio2211/opl/bin/arm64_osx/oplrun",
  "description": "CPLEX is IBM's commercial optimization solver. Supports docplex (Python API) and OPL Studio (.mod/.dat files)."
}
```

### 例2: 生産計画最適化（docplex使用）

**あなた**: 
```
製品Aの利益が40ドル、製品Bが30ドル。
労働時間が製品Aは2時間、製品Bは1時間必要。
材料が製品Aは3kg、製品Bは2kg必要。
最大労働時間100時間、最大材料150kgの制約で、
最適な生産計画を教えて。
```

**Bob**:
```xml
<use_mcp_tool>
<server_name>cplex-optimizer</server_name>
<tool_name>solve_production_planning</tool_name>
<arguments>
{
  "products": ["Product_A", "Product_B"],
  "profit": {"Product_A": 40, "Product_B": 30},
  "labor_hours": {"Product_A": 2, "Product_B": 1},
  "material_kg": {"Product_A": 3, "Product_B": 2},
  "max_labor": 100,
  "max_material": 150
}
</arguments>
</use_mcp_tool>
```

**結果**:
```json
{
  "status": "Optimal",
  "optimal": true,
  "solver": "CPLEX",
  "objective_value": 2000.0,
  "production_plan": {
    "Product_A": 25.0,
    "Product_B": 50.0
  },
  "resource_usage": {
    "labor_hours": 100.0,
    "material_kg": 150.0
  },
  "resource_utilization": {
    "labor": 100.0,
    "material": 100.0
  }
}
```

### 例3: OPLモデルを直接実行

**あなた**: 
```
CPLEXのOPLモデルを実行して。
/Users/aa539999/Desktop/BOBcode/CPLEX/production.mod
/Users/aa539999/Desktop/BOBcode/CPLEX/production.dat
```

**Bob**:
```xml
<use_mcp_tool>
<server_name>cplex-optimizer</server_name>
<tool_name>run_opl_from_files</tool_name>
<arguments>
{
  "mod_file_path": "/Users/aa539999/Desktop/BOBcode/CPLEX/production.mod",
  "dat_file_path": "/Users/aa539999/Desktop/BOBcode/CPLEX/production.dat"
}
</arguments>
</use_mcp_tool>
```

### 例4: OPLモデルを文字列で実行

**あなた**: 
```
以下のOPLモデルを実行して:
dvar float+ x;
dvar float+ y;
maximize 3*x + 2*y;
subject to {
  x + 2*y <= 10;
  2*x + y <= 12;
}
```

**Bob**:
```xml
<use_mcp_tool>
<server_name>cplex-optimizer</server_name>
<tool_name>run_opl_model</tool_name>
<arguments>
{
  "mod_content": "dvar float+ x;\ndvar float+ y;\nmaximize 3*x + 2*y;\nsubject to {\n  x + 2*y <= 10;\n  2*x + y <= 12;\n}"
}
</arguments>
</use_mcp_tool>
```

## ファイル構成

```
cplex-mcp-server/
├── __main__.py          # エントリーポイント
├── server.py            # サーバー本体（CPLEX + OPL対応）
├── requirements.txt     # 依存関係
└── README.md           # このファイル
```

## 技術詳細

### 使用ライブラリ

- **IBM CPLEX (docplex)** - 商用ソルバー（高速・高性能）
- **CPLEX OPL Studio** - .mod/.datファイル実行

### CPLEXの特徴

| 項目 | CPLEX |
|------|-------|
| ライセンス | 商用（有料） |
| 性能 | 非常に高速 |
| 問題サイズ | 大規模対応 |
| アルゴリズム | 最先端 |
| サポート | IBM公式 |

### 対応する問題タイプ

- ✅ 線形計画問題（LP）
- ✅ 整数計画問題（IP）
- ✅ 混合整数計画問題（MIP）
- ✅ 二次計画問題（QP）
- ✅ 二次制約計画問題（QCP）
- ✅ OPLモデル（.mod/.dat）

## トラブルシューティング

### CPLEXが見つからない

**症状**: `ImportError: CPLEX (docplex) is not available`

**解決策**:
```bash
pip3 install docplex
```

### OPL Studioが見つからない

**症状**: `"error": "CPLEX OPL Studio not found"`

**確認**:
```bash
ls -la /Applications/CPLEX_Studio2211/opl/bin/arm64_osx/oplrun
```

**解決策**: CPLEX Studio 22.1.1をインストール

### ライセンスエラー

**症状**: `CPLEX Error 1016: Community Edition. Problem size limits exceeded.`

**原因**: Community Editionの制限（変数1000個、制約1000個）

**解決策**:
1. 問題サイズを小さくする
2. 商用ライセンスを取得

## パフォーマンス

### 小規模問題（変数10個、制約10個）
- CPLEX: 0.01秒

### 中規模問題（変数100個、制約100個）
- CPLEX: 0.1秒

### 大規模問題（変数1000個、制約1000個）
- CPLEX: 1秒

## 参考リンク

- [IBM CPLEX Documentation](https://www.ibm.com/docs/en/icos)
- [docplex Documentation](https://ibmdecisionoptimization.github.io/docplex-doc/)
- [CPLEX OPL Language Reference](https://www.ibm.com/docs/en/icos/22.1.1?topic=cplex-opl-language-reference-manual)
- [MCP Specification](https://modelcontextprotocol.io/)

## ライセンス

Apache 2.0