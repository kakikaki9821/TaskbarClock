# TaskbarClock

Windows 11 のシステムトレイに常駐するデジタル時計アプリ。

## 機能

- **デジタル時計** — システムトレイにHH:MM表示
- **アナログ時計** — マウスホバーでポップアップ表示
- **目覚まし** — 複数登録、曜日繰り返し、スヌーズ
- **タイマー** — カウントダウン、プリセット付き
- **テーマ** — Windows 11 ダーク/ライトモード自動対応

## 必要環境

- Windows 11
- Python 3.10+

## インストール

```bash
pip install -r requirements.txt
```

## 使い方

```bash
python app.py
```

システムトレイに時計アイコンが表示されます。

- **マウスホバー** — アナログ時計をポップアップ表示
- **右クリック** — アラーム設定 / タイマー / 設定 / 終了

## 開発

```bash
pip install -r requirements.txt -r requirements-dev.txt

# テスト
pytest

# リント
ruff check .

# 型チェック
mypy clock/ core/

# exe化
pyinstaller --onefile --windowed --icon=resources/icon.ico app.py
```

## ライセンス

MIT
