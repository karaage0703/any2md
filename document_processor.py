"""
ドキュメント処理モジュール

マークダウン、テキスト、パワーポイント、PDFなどのファイルの読み込みと変換を行います。
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any
import hashlib
import time

import markitdown


class DocumentProcessor:
    """
    ドキュメント処理クラス

    マークダウン、テキスト、パワーポイント、PDFなどのファイルの読み込みと変換を行います。

    Attributes:
        logger: ロガー
    """

    # サポートするファイル拡張子
    SUPPORTED_EXTENSIONS = {
        "text": [".txt", ".md", ".markdown"],
        "office": [".ppt", ".pptx", ".doc", ".docx"],
        "pdf": [".pdf"],
    }

    def __init__(self):
        """
        DocumentProcessorのコンストラクタ
        """
        # ロガーの設定
        self.logger = logging.getLogger("document_processor")
        self.logger.setLevel(logging.INFO)

    def read_file(self, file_path: str) -> str:
        """
        ファイルを読み込みます。

        Args:
            file_path: ファイルのパス

        Returns:
            ファイルの内容

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            IOError: ファイルの読み込みに失敗した場合
        """
        try:
            # ファイル拡張子を取得
            ext = Path(file_path).suffix.lower()

            # テキストファイル（マークダウン含む）の場合
            if ext in self.SUPPORTED_EXTENSIONS["text"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # NUL文字を削除
                    content = content.replace("\x00", "")
                self.logger.info(f"テキストファイル '{file_path}' を読み込みました")
                return content

            # パワーポイント、Word、PDFの場合はmarkitdownを使用して変換
            elif ext in self.SUPPORTED_EXTENSIONS["office"] or ext in self.SUPPORTED_EXTENSIONS["pdf"]:
                return self.convert_to_markdown(file_path)

            # サポートしていない拡張子の場合
            else:
                self.logger.warning(f"サポートしていないファイル形式です: {file_path}")
                return ""

        except FileNotFoundError:
            self.logger.error(f"ファイル '{file_path}' が見つかりません")
            raise
        except IOError as e:
            self.logger.error(f"ファイル '{file_path}' の読み込みに失敗しました: {str(e)}")
            raise

    def convert_to_markdown(self, file_path: str) -> str:
        """
        パワーポイント、Word、PDFなどのファイルをマークダウンに変換します。

        Args:
            file_path: ファイルのパス

        Returns:
            マークダウンに変換された内容

        Raises:
            Exception: 変換に失敗した場合
        """
        try:
            # ファイルURIを作成
            file_uri = f"file://{os.path.abspath(file_path)}"

            # markitdownを使用して変換
            markdown_content = markitdown.MarkItDown().convert_uri(file_uri).markdown
            # NUL文字を削除
            markdown_content = markdown_content.replace("\x00", "")

            self.logger.info(f"ファイル '{file_path}' をマークダウンに変換しました")
            return markdown_content
        except Exception as e:
            self.logger.error(f"ファイル '{file_path}' のマークダウン変換に失敗しました: {str(e)}")
            raise

    def calculate_file_hash(self, file_path: str) -> str:
        """
        ファイルのハッシュ値を計算します。

        Args:
            file_path: ファイルのパス

        Returns:
            ファイルのSHA-256ハッシュ値
        """
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            self.logger.error(f"ファイル '{file_path}' のハッシュ計算に失敗しました: {str(e)}")
            # エラーが発生した場合は、タイムスタンプをハッシュとして使用
            return f"timestamp-{int(time.time())}"

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        ファイルのメタデータを取得します。

        Args:
            file_path: ファイルのパス

        Returns:
            ファイルのメタデータ（ハッシュ値、最終更新日時など）
        """
        file_stat = os.stat(file_path)
        return {
            "hash": self.calculate_file_hash(file_path),
            "mtime": file_stat.st_mtime,
            "size": file_stat.st_size,
            "path": file_path,
        }

    def load_file_registry(self, processed_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        処理済みファイルのレジストリを読み込みます。

        Args:
            processed_dir: 処理済みファイルを保存するディレクトリのパス

        Returns:
            処理済みファイルのレジストリ（ファイルパスをキーとするメタデータの辞書）
        """
        registry_path = Path(processed_dir) / "file_registry.json"
        if not registry_path.exists():
            return {}

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"ファイルレジストリの読み込みに失敗しました: {str(e)}")
            return {}

    def save_file_registry(self, processed_dir: str, registry: Dict[str, Dict[str, Any]]) -> None:
        """
        処理済みファイルのレジストリを保存します。

        Args:
            processed_dir: 処理済みファイルを保存するディレクトリのパス
            registry: 処理済みファイルのレジストリ
        """
        registry_path = Path(processed_dir) / "file_registry.json"
        try:
            # 処理済みディレクトリが存在しない場合は作成
            os.makedirs(Path(processed_dir), exist_ok=True)

            with open(registry_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)
            self.logger.info(f"ファイルレジストリを保存しました: {registry_path}")
        except Exception as e:
            self.logger.error(f"ファイルレジストリの保存に失敗しました: {str(e)}")
