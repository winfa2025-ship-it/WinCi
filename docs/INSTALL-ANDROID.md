# WinCi Android 安裝

## 下載

- APK：https://github.com/winfa2025-ship-it/WinCi/releases/download/v0.1.4/WinCi.apk
- Release：https://github.com/winfa2025-ship-it/WinCi/releases/tag/v0.1.4

## 手機步驟

1. 下載 `WinCi.apk`
2. 允許「安裝未知應用程式」
3. 安裝並開啟 WinCi
4. **登入頁** Engine URL 預設已係 `https://sitemixhk.com/winci-api`（網站伺服器）。開 App 應自動綠燈；舊版若仲留住 LAN IP，按「儲存連線」或清 App 資料。
5. 用 **電郵**／**Demo** 登入；真 Google 見 [GOOGLE-LOGIN.md](./GOOGLE-LOGIN.md)
6. 電腦同一 Wi‑Fi 跑：`bash scripts/install-desktop.sh`

Package id：`com.winci.app` · 專案：`apps/android`（Capacitor）

## Google 登入

Android WebView **唔得**用網頁 Google 彈窗。v0.1.4+ 用原生 Google Sign-In。  
要自己喺 Google Cloud 建 Web + Android OAuth client，步驟：[GOOGLE-LOGIN.md](./GOOGLE-LOGIN.md)。

## 注意

源碼 zip **唔係**安裝包。Debug APK 用 debug 簽名，適合個人側載。
