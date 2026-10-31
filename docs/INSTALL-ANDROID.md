# WinCi Android 安裝

## 下載

- APK：https://github.com/winfa2025-ship-it/WinCi/releases/download/v0.1.3/WinCi.apk
- Release：https://github.com/winfa2025-ship-it/WinCi/releases/tag/v0.1.3

## 手機步驟

1. 下載 `WinCi.apk`
2. 允許「安裝未知應用程式」
3. 安裝並開啟 WinCi
4. Settings → **Engine URL** → 填 `http://電腦LAN_IP:8787`
5. 電腦同一 Wi‑Fi 跑：`bash scripts/install-desktop.sh`

Package id：`com.winci.app` · 專案：`apps/android`（Capacitor）

## 注意

源碼 zip **唔係**安裝包。Debug APK 用 debug 簽名，適合個人側載。
