# WinCi Google 登入設定

## 點解 APK 以前登入唔到 Google？

1. **未設 `GOOGLE_CLIENT_ID` / Web Client ID** — 舊版只得 Demo，或按鈕叫「Google」但其實冇真 OAuth。
2. **Android WebView 禁止 Google 登入彈窗** — 唔可以靠網頁 GIS popup；要用 **原生 Google Sign-In**（本版已接 `@southdevs/capacitor-google-auth`）。
3. **登入畫面擋住 Settings** — 舊版要先訪客先填 Engine URL；而家登入頁可直接填 Engine URL + Client ID。

## 你要做嘅（真 Google 帳號）

### A. Google Cloud Console

1. 開 [Google Cloud Console](https://console.cloud.google.com/) → 選專案（或新建 `WinCi`）
2. **APIs & Services → OAuth consent screen**：External（個人用），填 App 名 WinCi，加自己電郵為測試用戶
3. **Credentials → Create credentials → OAuth client ID**

#### 1）Web application（必備 — 用作 ID token audience）

- Application type: **Web application**
- Name: `WinCi Web`
- Authorized JavaScript origins（可加）：
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - `https://localhost`（Capacitor Android WebView）
- 複製 **Client ID**（`…..apps.googleusercontent.com`）

#### 2）Android（APK 必備）

- Application type: **Android**
- Name: `WinCi Android`
- Package name: **`com.winci.app`**
- SHA-1（本專案 **debug** keystore）：

```
78:2B:6A:79:DC:53:6F:A8:69:10:EF:D6:51:67:11:1F:D9:43:D3:3F
```

自行再算（本機 debug keystore）：

```bash
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

> Release 簽名要另加一條 Android client（用 release keystore 嘅 SHA-1）。

### B. 填入 WinCi

**手機 APK**

1. 開 WinCi → 登入頁
2. **Engine URL** → `http://你電腦LAN_IP:8787` →「儲存連線」（燈變綠）
3. **Google Web Client ID** → 貼 Web client 嗰條 →「儲存連線」
4. 按 **Google 登入**（會開系統 Google 帳戶選擇器）

**電腦引擎 `.env`**

```env
GOOGLE_CLIENT_ID=你的WebClientId.apps.googleusercontent.com
```

（登入頁「儲存」亦會 `POST /auth/google/client-id` 寫入引擎 session，唔使一定改 .env。）

**Web 開發**

```env
# apps/web/.env
VITE_GOOGLE_CLIENT_ID=你的WebClientId.apps.googleusercontent.com
```

## 冇 Client ID 時

- **電郵註冊／登入** — 照常（本機 SQLite + JWT）
- **Demo 登入** — 本機假帳 `demo@winci.local`（唔係真 Google）

## 技術摘要

| 平台 | 方式 |
|------|------|
| Android APK | 原生 Google Sign-In → idToken → `POST /auth/google` |
| 瀏覽器 | Google Identity Services → credential → 同上 |
| 引擎 | `tokeninfo` 驗 `aud` == Web Client ID |

Package：`com.winci.app` · 版本見 Release notes。
