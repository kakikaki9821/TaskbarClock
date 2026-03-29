# TaskbarClock - Windows 11 タスクバー時計アプリ

## プロジェクト概要
Windows 11のシステムトレイに常駐するデジタル時計。目覚まし・タイマー機能付き、マウスオーバーでアナログ時計表示。製品レベル品質。

## 技術スタック
- Python 3.10+ / PySide6（UI）
- darkdetect + pyqtdarktheme（テーマ）
- win11toast（通知）
- Loguru（ログ）/ Sentry（クラッシュレポート）
- gettext/Babel（i18n）
- PyInstaller（exe化）/ Inno Setup（インストーラー）
- pytest + pytest-qt（テスト）

## エージェントチーム（5名）
- `qt-developer`: PySide6 UI開発・システムトレイ・アナログ時計描画
- `windows-engineer`: サウンド・通知・自動起動・Windows API
- `build-engineer`: PyInstaller exe化・Inno Setup・CI/CD・自動アップデート
- `release-manager`: ログ・クラッシュレポート・テーマ・i18n・アクセシビリティ
- `qa-tester`: テスト・品質検証・メモリリーク検出

## 開発ルール
- 全Claudeファイルはプロジェクトフォルダ内に保管
- 日本語で開発・コミュニケーション
- コマンド確認不要（settings.local.jsonで自動許可）

## ドキュメント
- `.claude/plans/taskbar-clock-plan.md` — 実装計画（製品レベル）
