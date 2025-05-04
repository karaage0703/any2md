#!/usr/bin/env python3
"""
any2md - 様々な形式のファイルをマークダウンに変換するツール

使用方法:
  python main.py [オプション]

オプション:
  --source-dir SOURCE_DIR    原稿ファイルが含まれるディレクトリのパス（デフォルト: ./source）
  --processed-dir PROCESSED_DIR    処理済みファイルを保存するディレクトリのパス（デフォルト: ./processed）
  --incremental    差分のみを処理する（デフォルト: False）
  --log-file LOG_FILE    ログファイルのパス（デフォルト: any2md.log）
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}    ログレベル（デフォルト: INFO）
  --version    バージョン情報を表示して終了
  --help    このヘルプメッセージを表示して終了
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from document_processor import DocumentProcessor


def setup_logging(log_file, log_level):
    """
    ロギングの設定を行います。

    Args:
        log_file: ログファイルのパス
        log_level: ログレベル
    """
    # ログレベルの文字列を定数に変換
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"無効なログレベルです: {log_level}")

    # ロガーの設定
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # フォーマッタの作成
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # ファイルハンドラの設定
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def parse_arguments():
    """
    コマンドライン引数を解析します。

    Returns:
        解析されたコマンドライン引数
    """
    parser = argparse.ArgumentParser(description="any2md - 様々な形式のファイルをマークダウンに変換するツール")
    parser.add_argument(
        "--source-dir",
        default="./source",
        help="原稿ファイルが含まれるディレクトリのパス（デフォルト: ./source）",
    )
    parser.add_argument(
        "--processed-dir",
        default="./processed",
        help="処理済みファイルを保存するディレクトリのパス（デフォルト: ./processed）",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="差分のみを処理する（デフォルト: False）",
    )
    parser.add_argument(
        "--log-file",
        default="any2md.log",
        help="ログファイルのパス（デフォルト: any2md.log）",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="ログレベル（デフォルト: INFO）",
    )
    parser.add_argument("--version", action="version", version="any2md 1.0.0", help="バージョン情報を表示して終了")

    return parser.parse_args()


def convert_files(processor, source_dir, processed_dir, incremental=False):
    """
    ディレクトリ内のファイルをマークダウンに変換します。

    Args:
        processor: DocumentProcessorのインスタンス
        source_dir: 原稿ファイルが含まれるディレクトリのパス
        processed_dir: 処理済みファイルを保存するディレクトリのパス
        incremental: 差分のみを処理するかどうか

    Returns:
        処理したファイルの数
    """
    logger = logging.getLogger()
    source_directory = Path(source_dir)

    if not source_directory.exists() or not source_directory.is_dir():
        logger.error(f"ディレクトリ '{source_dir}' が見つからないか、ディレクトリではありません")
        raise FileNotFoundError(f"ディレクトリ '{source_dir}' が見つからないか、ディレクトリではありません")

    # サポートするファイル拡張子を全て取得
    all_extensions = []
    for ext_list in processor.SUPPORTED_EXTENSIONS.values():
        all_extensions.extend(ext_list)

    # ファイルを検索
    files = []
    for ext in all_extensions:
        files.extend(list(source_directory.glob(f"**/*{ext}")))

    logger.info(f"ディレクトリ '{source_dir}' 内に {len(files)} 個のファイルが見つかりました")

    # 差分処理の場合、ファイルレジストリを読み込む
    if incremental:
        file_registry = processor.load_file_registry(processed_dir)
        logger.info(f"ファイルレジストリから {len(file_registry)} 個のファイル情報を読み込みました")
    else:
        file_registry = {}

    # 処理対象のファイルを特定
    files_to_process = []
    for file_path in files:
        str_path = str(file_path)
        if incremental:
            # ファイルのメタデータを取得
            current_metadata = processor.get_file_metadata(str_path)

            # レジストリに存在しない、またはハッシュ値が変更されている場合のみ処理
            if (
                str_path not in file_registry
                or file_registry[str_path]["hash"] != current_metadata["hash"]
                or file_registry[str_path]["mtime"] != current_metadata["mtime"]
                or file_registry[str_path]["size"] != current_metadata["size"]
            ):
                files_to_process.append(file_path)
                # レジストリを更新
                file_registry[str_path] = current_metadata
        else:
            # 差分処理でない場合は全てのファイルを処理
            files_to_process.append(file_path)
            # レジストリを更新
            file_registry[str_path] = processor.get_file_metadata(str_path)

    logger.info(f"処理対象のファイル数: {len(files_to_process)} / {len(files)}")

    # 各ファイルを処理
    processed_count = 0
    for file_path in files_to_process:
        try:
            # ファイルを読み込む
            content = processor.read_file(str(file_path))
            if not content:
                continue

            # ファイルパスからディレクトリ構造を取得
            file_path_obj = Path(file_path)
            try:
                # sourceディレクトリからの相対パスを取得
                relative_path = file_path_obj.relative_to(Path(source_dir))
                parent_dirs = relative_path.parent.parts

                # ディレクトリ名をサフィックスとして使用（サブディレクトリがある場合のみ）
                dir_suffix = "_".join(parent_dirs) if parent_dirs else ""
            except ValueError:
                # 相対パスの取得に失敗した場合は空文字列を使用
                dir_suffix = ""

            # 処理済みファイル名を生成
            processed_file_name = f"{file_path_obj.stem}{('_' + dir_suffix) if dir_suffix else ''}.md"
            processed_file_path = Path(processed_dir) / processed_file_name

            # 処理済みディレクトリが存在しない場合は作成
            os.makedirs(Path(processed_dir), exist_ok=True)

            # 処理済みファイルに書き込む
            with open(processed_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"処理済みファイルを保存しました: {processed_file_path}")
            processed_count += 1

        except Exception as e:
            logger.error(f"ファイル '{file_path}' の処理中にエラーが発生しました: {str(e)}")
            # エラーが発生しても処理を続行
            continue

    # ファイルレジストリを保存
    processor.save_file_registry(processed_dir, file_registry)

    logger.info(f"ディレクトリ '{source_dir}' 内のファイルを処理しました（合計 {processed_count} ファイル）")
    return processed_count


def main():
    """
    メイン関数
    """
    # コマンドライン引数の解析
    args = parse_arguments()

    # ロギングの設定
    logger = setup_logging(args.log_file, args.log_level)
    logger.info("any2md を開始します")

    try:
        # ディレクトリのパスを絶対パスに変換
        source_dir = os.path.abspath(args.source_dir)
        processed_dir = os.path.abspath(args.processed_dir)

        # ディレクトリの存在確認
        if not os.path.exists(source_dir):
            logger.error(f"ソースディレクトリが見つかりません: {source_dir}")
            sys.exit(1)

        # 処理済みディレクトリが存在しない場合は作成
        os.makedirs(processed_dir, exist_ok=True)

        logger.info(f"ソースディレクトリ: {source_dir}")
        logger.info(f"処理済みディレクトリ: {processed_dir}")
        logger.info(f"差分処理: {args.incremental}")

        # DocumentProcessorのインスタンスを作成
        processor = DocumentProcessor()

        # ファイルを変換
        processed_count = convert_files(
            processor=processor,
            source_dir=source_dir,
            processed_dir=processed_dir,
            incremental=args.incremental,
        )

        logger.info(f"処理が完了しました。合計 {processed_count} ファイルが変換されました。")

    except Exception as e:
        logger.exception(f"処理中にエラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
