# any2md

様々な形式のファイル（PDF、PowerPoint、Word、テキストなど）をマークダウンに変換するツールです。

## 機能

- PDF、PowerPoint、Word、テキストファイルをマークダウンに変換
- ディレクトリ内のファイルを一括変換
- 差分処理（変更されたファイルのみを処理）
- ファイルレジストリによる処理履歴の管理

## 必要条件

- Python 3.6以上
- markitdownライブラリ

## インストール

### pipを使用する場合

```bash
# 必要なライブラリをインストール
pip install "markitdown[all]"
```

### uvを使用する場合

[uv](https://github.com/astral-sh/uv) は高速な Python パッケージマネージャーで、pip の代替として使用できます。

```bash
# 仮想環境を作成
uv venv

# 仮想環境をアクティブ化
source .venv/bin/activate

# 必要なライブラリをインストール
uv pip install "markitdown[all]"
```

## 使い方

### 基本的な使い方

```bash
# sourceディレクトリ内のファイルをprocessedディレクトリに変換
python main.py
```

### オプション

```bash
# ヘルプを表示
python main.py --help

# カスタムディレクトリを指定
python main.py --source-dir ./my_documents --processed-dir ./output

# 差分処理（変更されたファイルのみを処理）
python main.py --incremental

# ログレベルを変更
python main.py --log-level DEBUG
```

## ディレクトリ構造

- `source/`: 変換元のファイルを配置するディレクトリ
- `processed/`: 変換後のマークダウンファイルが保存されるディレクトリ

## サポートしているファイル形式

- テキスト: `.txt`, `.md`, `.markdown`
- オフィス文書: `.ppt`, `.pptx`, `.doc`, `.docx`
- PDF: `.pdf`

## ライセンス

MITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。