# Contributing to TaskbarClock

TaskbarClock への貢献を歓迎します。

## 開発環境のセットアップ

```bash
git clone https://github.com/kakikaki9821/TaskbarClock.git
cd TaskbarClock
pip install -r requirements.txt -r requirements-dev.txt
```

## 開発ワークフロー

### 1. ブランチ作成
```bash
git checkout -b feature/your-feature-name
```

### 2. コーディング規約
- **リンター**: ruff（デフォルトルール）
- **フォーマッター**: ruff format
- **型チェック**: mypy（`disallow_untyped_defs = true`）
- **型ヒント**: 全関数に必須

```bash
ruff check .          # リント
ruff format .         # フォーマット
mypy clock/ core/     # 型チェック
```

### 3. テスト
```bash
pytest                                    # 全テスト
pytest tests/unit/                        # ユニットテストのみ
pytest tests/unit/test_alarm.py -v        # 特定ファイル
pytest --cov=clock --cov=core             # カバレッジ付き
```

### 4. コミット
```bash
git add <files>
git commit -m "feat: 機能の説明"
```

コミットメッセージの形式:
- `feat:` — 新機能
- `fix:` — バグ修正
- `refactor:` — リファクタリング
- `docs:` — ドキュメント
- `test:` — テスト追加
- `style:` — フォーマット修正
- `ci:` — CI/CD変更

### 5. プルリクエスト
```bash
git push origin feature/your-feature-name
```
GitHub上でPull Requestを作成してください。

## アーキテクチャルール

### レイヤー依存方向
```
ui/ → clock/ → core/
ui/ → services/ → core/
```

**`clock/`層はPySide6をimportしない。** 純粋Pythonのみ。

### テスト
- 新機能にはユニットテストを追加すること
- ビジネスロジック（`clock/`）のカバレッジ90%以上を維持
- テスト時の時刻制御は `FakeClock` フィクスチャを使用

## Issue / バグ報告

[Issues](https://github.com/kakikaki9821/TaskbarClock/issues)から報告してください。

テンプレート:
```
### 環境
- Windows バージョン:
- Python バージョン:
- TaskbarClock バージョン:

### 再現手順
1.
2.

### 期待する動作

### 実際の動作

### ログ（あれば）
```

## ライセンス

MIT License。詳細は [LICENSE](LICENSE) を参照してください。
