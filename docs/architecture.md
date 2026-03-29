# TaskbarClock アーキテクチャドキュメント

## 概要

TaskbarClock は Windows 11 のタスクバーに常駐するデジタル時計アプリです。PySide6 (Qt) を使用し、4層のレイヤードアーキテクチャで構成されています。

---

## レイヤー構成

```
┌─────────────────────────────────────────────────────────┐
│                    app.py                                │
│              ApplicationController                       │
│         初期化 → シグナル接続 → イベントループ              │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  ui/        │  │  clock/     │  │  core/      │
│ (プレゼン)   │  │ (ビジネス)   │  │ (基盤)      │
├─────────────┤  ├─────────────┤  ├─────────────┤
│ tray_icon   │  │ alarm       │  │ config      │
│ taskbar_    │  │ timer_      │  │ logger      │
│  clock_     │  │  manager    │  │ crash_report│
│  widget     │  │             │  │ singleton   │
│ analog_clock│  │             │  │             │
│ clock_      │  │             │  │             │
│  renderer   │  │             │  │             │
│ alarm_dialog│  │             │  │             │
│ timer_dialog│  │             │  │             │
│ theme       │  │             │  │             │
└──────┬──────┘  └─────────────┘  └──────┬──────┘
       │                                 │
       └──────────┐    ┌─────────────────┘
                  ▼    ▼
           ┌─────────────┐
           │  services/  │
           │ (外部I/O)    │
           ├─────────────┤
           │ sounds      │
           │ notifier    │
           └─────────────┘
```

### 依存ルール（厳守）

```
ui/ ──→ clock/ ──→ core/
 │                   ↑
 └──→ services/ ─────┘

禁止: clock/ → ui/    (importしない)
禁止: core/  → clock/ (importしない)
禁止: core/  → ui/    (importしない)
```

**`clock/`層はPySide6を一切importしない。** 時刻はdatetime標準ライブラリのみ使用し、純粋なPythonロジックとしてテスト可能にする。

---

## モジュール詳細

### core/ — 基盤サービス

| ファイル | 責務 |
|---------|------|
| `config.py` | JSON設定管理。デバウンス保存（500ms）、アトミック書込み、破損時リカバリ |
| `logger.py` | Loguru設定。コンソール+ファイル出力、500MBローテーション、30日保持 |
| `crash_report.py` | Sentry SDK初期化。環境変数`TASKBAR_CLOCK_SENTRY_DSN`から読取 |
| `singleton.py` | QSharedMemoryによる二重起動防止 |

### clock/ — ビジネスロジック（Qt非依存）

| ファイル | 責務 |
|---------|------|
| `alarm.py` | `Alarm`データクラス（バリデーション付き）+ `AlarmManager`（クロック注入、多重リスナー） |
| `timer_manager.py` | `TimerManager` 状態機械。`on_tick()/on_finished()/on_state_changed()`で多重リスナー対応 |

### services/ — 外部I/O

| ファイル | 責務 |
|---------|------|
| `sounds.py` | `SoundPlayer` — 3段フォールバック: QMediaPlayer → winsound(別スレッド) → SystemBeep |
| `notifier.py` | `Notifier` — win11toast トースト通知。スヌーズコールバック対応 |

### ui/ — プレゼンテーション（PySide6依存）

| ファイル | 責務 |
|---------|------|
| `tray_icon.py` | `TrayIcon` — システムトレイアイコン。分単位キャッシュ描画、右クリックメニュー |
| `taskbar_clock_widget.py` | `TaskbarClockWidget` — フローティング時計。ドラッグ移動、サイズプリセット、位置永続化 |
| `analog_clock.py` | `AnalogClock` — フレームレスポップアップ。60fps秒針、表示時のみタイマー動作 |
| `clock_renderer.py` | `ClockRenderer` — デジタル/アナログ描画。針角度計算は純粋関数（テスト可能） |
| `alarm_dialog.py` | `AlarmDialog` — アラーム管理UI。追加/削除/ON-OFF |
| `timer_dialog.py` | `TimerDialog` — タイマーUI。プリセット、状態連動表示 |
| `theme.py` | `ThemeManager` — darkdetect + qdarktheme。リアルタイムテーマ追従 |

---

## データフロー

### 時計表示

```
QTimer(1000ms)
    │
    ├──→ TrayIcon._update_icon()
    │       └──→ ClockRenderer.render_digital() [分単位キャッシュ]
    │
    └──→ TaskbarClockWidget._update_time() [分変更時のみ再描画]

TrayIcon.activated / Widget.left_clicked
    └──→ AnalogClock.toggle_at_tray()
            └──→ QTimer(16ms) → ClockRenderer.render_analog() [表示時のみ]
```

### アラーム

```
QTimer(1000ms) ──→ AlarmManager.check()
                       │
                       ├──→ SoundPlayer.play()
                       └──→ Notifier.show_alarm()
                                │
                                └──→ スヌーズ → AlarmManager.snooze()

AlarmDialog ──→ AlarmManager.add/remove/update()
                       │
                       └──→ Config.save_debounced()
```

### タイマー

```
QTimer(100ms) ──→ TimerManager.tick(100)
                       │
                       ├──→ [tick listeners] → TrayIcon tooltip更新
                       │                     → TimerDialog 表示更新
                       │
                       └──→ [finished] → SoundPlayer.play()
                                        → Notifier.show_timer_done()

TimerDialog ──→ TimerManager.start/pause/resume/cancel()
```

---

## 状態管理

### タイマー状態遷移

```
IDLE ──start()──→ RUNNING
                    │
                    ├──pause()──→ PAUSED
                    │               │
                    │   ←resume()───┘
                    │
                    ├──tick(0)──→ FINISHED ──dismiss()──→ IDLE
                    │
                    └──cancel()──→ IDLE

PAUSED ──cancel()──→ IDLE
```

### 設定永続化

```
Config (JSON)
  ├── load: ファイル読込 → パース → 破損時デフォルト復元+バックアップ
  ├── save: デバウンス(500ms) → 一時ファイル書込 → atomicリネーム
  └── shutdown: save_immediate() で即座保存
```

---

## 初期化順序

```python
1. Logger          # 最優先（以降のエラーを全て捕捉）
2. Config          # 設定読込（破損時はデフォルト復元）
3. Sentry          # クラッシュレポート
4. QApplication    # Qtイベントループ基盤
5. Singleton       # 二重起動防止
6. ThemeManager    # ダーク/ライト検出
7. ClockRenderer   # 描画エンジン
8. SoundPlayer     # サウンド再生
9. AlarmManager    # アラーム状態復元
10. TimerManager   # タイマー（QTimerドライバー付き）
11. Notifier       # トースト通知
12. TrayIcon       # システムトレイ
13. ClockWidget    # フローティング時計
14. AnalogClock    # ポップアップ時計
15. Signal接続     # 全コンポーネント連携
```

---

## デザインパターン

| パターン | 適用箇所 | 目的 |
|---------|---------|------|
| **Singleton** | `core/singleton.py` | 二重起動防止 |
| **Observer** | TimerManager の多重リスナー | ダイアログ非依存のイベント通知 |
| **Signal/Slot** | Qt全コンポーネント間 | 疎結合な通信 |
| **Strategy/Fallback** | `services/sounds.py` | 3段サウンド再生 |
| **State Machine** | `TimerManager` | 明示的な状態遷移 |
| **DI (Dependency Injection)** | AlarmManager(clock=) | テスト時の時刻制御 |
| **Composition Root** | `ApplicationController` | 全オブジェクト生成を一箇所に集約 |

---

## テスト戦略

```
tests/
├── unit/           # 純粋ロジック (Qt不要、高速)
│   ├── test_alarm.py          # Alarm判定、バリデーション、シリアライズ
│   ├── test_timer.py          # 状態遷移、多重リスナー、境界値
│   ├── test_clock_renderer.py # 針角度計算
│   ├── test_config.py         # 永続化、破損リカバリ、デバウンス
│   └── test_sounds.py         # フォールバックチェーン（モック）
├── integration/    # Qt GUI (pytest-qt)
│   ├── test_tray_icon.py      # トレイアイコン生成、メニュー
│   ├── test_analog_clock.py   # ポップアップ表示/非表示
│   ├── test_alarm_dialog.py   # ダイアログ操作
│   └── test_timer_dialog.py   # プリセット、シグナル
└── e2e/            # 全体フロー
    └── test_app_lifecycle.py  # インポート、設定往復、アラーム→タイマーフロー
```

### カバレッジ目標

| レイヤー | 目標 | 現状 |
|---------|------|------|
| `clock/` | 90%+ | 95-97% |
| `core/` | 80%+ | 92% |
| `services/` | 70%+ | モックベース |
| `ui/` | 50%+ | 統合テストで補完 |
