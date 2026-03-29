# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-03-29

### Added
- System tray digital clock (HH:MM) with 1-second tooltip updates
- Analog clock popup on mouse hover with smooth second hand (60fps)
- Multiple alarms with weekday repeat, on/off toggle, and 5-minute snooze
- Countdown timer with presets (1/3/5/10/30 minutes)
- Windows 11 dark/light theme auto-detection and real-time switching
- Toast notifications for alarms and timer completion
- 3-level sound fallback (QMediaPlayer → winsound → SystemBeep)
- JSON config with debounced atomic writes and corruption recovery
- Single instance enforcement (prevents double launch)
- High DPI and multi-monitor support
- Accessibility labels for screen readers (NVDA/Narrator)
- Loguru structured logging with file rotation
- Sentry crash reporting
- PyInstaller exe packaging
- Inno Setup installer with auto-start option
- GitHub Actions CI/CD (lint → test → build → release)
- 63 unit tests with 95%+ coverage on business logic
