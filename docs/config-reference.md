# TaskbarClock 設定リファレンス

## 設定ファイルの場所

```
Windows: C:\Users\<ユーザー名>\.taskbar-clock\config.json
```

## 設定項目

### alarms
- **型**: `array`
- **デフォルト**: `[]`
- **説明**: 登録されたアラームの一覧

各アラームのフォーマット:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "hour": 7,
  "minute": 0,
  "days": [0, 1, 2, 3, 4],
  "enabled": true,
  "label": "朝のアラーム"
}
```

| フィールド | 型 | 範囲 | 説明 |
|-----------|------|------|------|
| `id` | string | UUID | 一意識別子（自動生成） |
| `hour` | int | 0-23 | 時 |
| `minute` | int | 0-59 | 分 |
| `days` | int[] | 0-6 | 曜日（0=月, 1=火, ..., 6=日） |
| `enabled` | bool | - | 有効/無効 |
| `label` | string | - | ラベル（任意） |

### theme
- **型**: `string`
- **デフォルト**: `"auto"`
- **選択肢**: `"auto"`, `"dark"`, `"light"`
- **説明**: UIテーマ。`"auto"`はWindows設定に追従

### auto_start
- **型**: `bool`
- **デフォルト**: `false`
- **説明**: Windows起動時の自動実行（インストーラー版で設定）

### clock_size
- **型**: `string`
- **デフォルト**: `"medium"`
- **選択肢**: `"small"`, `"medium"`, `"large"`, `"xlarge"`
- **説明**: フローティング時計ウィジェットのサイズ

| 値 | サイズ | フォント |
|----|-------|---------|
| `"small"` | 60x24px | 10pt |
| `"medium"` | 80x32px | 14pt |
| `"large"` | 110x40px | 18pt |
| `"xlarge"` | 140x50px | 24pt |

### clock_position
- **型**: `array` or `null`
- **デフォルト**: `null`
- **フォーマット**: `[x, y]`（ピクセル座標）
- **説明**: フローティング時計の画面上の位置。`null`の場合は自動配置（タスクバー付近）

### window_opacity
- **型**: `float`
- **デフォルト**: `0.95`
- **範囲**: `0.0` - `1.0`
- **説明**: ウィンドウの不透明度（将来使用）

## 設定ファイルの例

```json
{
  "alarms": [
    {
      "id": "a1b2c3d4-...",
      "hour": 7,
      "minute": 0,
      "days": [0, 1, 2, 3, 4],
      "enabled": true,
      "label": "起床"
    },
    {
      "id": "e5f6g7h8-...",
      "hour": 12,
      "minute": 30,
      "days": [0, 1, 2, 3, 4],
      "enabled": true,
      "label": "昼休み"
    }
  ],
  "theme": "auto",
  "auto_start": false,
  "clock_size": "medium",
  "clock_position": [1200, 1050],
  "window_opacity": 0.95
}
```

## 破損リカバリ

設定ファイルが破損した場合（不正なJSON等）:
1. 破損ファイルが `config.json.corrupted` としてバックアップされます
2. デフォルト設定で新しい `config.json` が作成されます
3. アプリは正常に起動します

## ログファイル

```
C:\Users\<ユーザー名>\.taskbar-clock\logs\
├── taskbar_clock_2026-03-29.log
├── taskbar_clock_2026-03-28.log
└── ...
```

- **ローテーション**: 500MB
- **保持期間**: 30日
- **圧縮**: zip（古いログ）
- **フォーマット**: `YYYY-MM-DD HH:mm:ss.SSS | LEVEL | module:function:line | message`
