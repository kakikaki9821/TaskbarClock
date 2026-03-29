# TaskbarClock

[![CI](https://github.com/kakikaki9821/TaskbarClock/actions/workflows/ci.yml/badge.svg)](https://github.com/kakikaki9821/TaskbarClock/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Windows 11 のタスクバーに常時表示されるデジタル時計アプリ。

## 機能

- **常時表示時計** — タスクバー上にHH:MM表示（ドラッグ移動・サイズ変更可能）
- **アナログ時計** — クリックでポップアップ表示（60fps秒針）
- **目覚まし** — 複数登録、曜日繰り返し、スヌーズ5分、トースト通知
- **タイマー** — カウントダウン、プリセット（1/3/5/10/30分）
- **テーマ** — Windows 11 ダーク/ライトモード自動対応

## 使い方

### exeで実行（推奨）
[Releases](https://github.com/kakikaki9821/TaskbarClock/releases)からTaskbarClock.exeをダウンロードして実行。

### Pythonで実行
```bash
pip install -r requirements.txt
python app.py
```

### 操作方法
- **左クリック** — アナログ時計の表示/非表示
- **右クリック** — メニュー（サイズ変更 / アラーム / タイマー / 終了）
- **ドラッグ** — 時計の位置を移動

サイズと位置は自動保存され、次回起動時に復元されます。

## 開発

```bash
pip install -r requirements.txt -r requirements-dev.txt

pytest                        # テスト実行
ruff check .                  # リント
ruff format .                 # フォーマット
mypy clock/ core/             # 型チェック
```

### アーキテクチャ
```
clock/      純粋ビジネスロジック（Qt非依存）
core/       基盤サービス（設定・ログ・クラッシュレポート）
services/   外部I/O（サウンド・通知）
ui/         全UI要素（PySide6）
tests/      unit / integration / e2e
```

### ビルド（Windows上で実行）
```bash
pyinstaller --onefile --windowed --name=TaskbarClock --add-data "resources;resources" app.py
```

## ライセンス

MIT
