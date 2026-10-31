# WinCi（個人短炒 App）

海琋自用加密貨幣短炒儀表板。

## 安裝（Android APK）

> **zip／源碼 ≠ 安裝包。** GitHub 的 Source code zip 係源碼，唔會自動安裝。
>
> **要安裝請下載 APK**，喺手機開啟並允許「未知來源／安裝未知應用程式」。

1. 下載：**[WinCi.apk](https://github.com/winfa2025-ship-it/WinCi/releases/download/v0.1.3/WinCi.apk)**（Release [v0.1.3](https://github.com/winfa2025-ship-it/WinCi/releases/tag/v0.1.3)）
2. 用檔案管理員開啟 APK → 允許安裝
3. 開 App → **Settings → Engine URL** 填 `http://你電腦的LAN_IP:8787`（電腦要先跑引擎，同一 Wi‑Fi）
4. 電腦跑引擎：`bash scripts/install-desktop.sh` 或見下方「點跑」

### 其他安裝方式

- **電腦一鍵**：`bash scripts/install-desktop.sh` → 瀏覽器開 http://127.0.0.1:5173
- **PWA 加到主畫面**：用 Chrome／Edge 開上述網址 → 選單 →「安裝應用程式」或「加到主畫面」
- **自己編譯 APK**：需要 JDK + Android SDK，然後 `bash scripts/build-android-apk.sh`

## 功能

- 深色交易 UI（PWA）：行情、圖表 stub、下單（數量＋價錢）、機械人／**AutoEarn**、**100 信號板**、持倉、設定
- **電郵＋Google 登入**（本機 JWT；未設 `GOOGLE_CLIENT_ID` 可用 Demo Google）
- 預設 **紙上交易**；可選連幣安（v0.1.x LIVE 為 stub）
- **幣安 IP 白名單**備忘＋偵測引擎對外 IP
- 最低名義 **1 美金**；倉位上限；日虧 kill-switch
- 可選 **DeepSeek** AI 短評／信號微調；冇 key 紙上照常跑
- **連線燈**：綠＝已連接，紅＝未設定（Auth／Binance／DeepSeek／Bot）
- **短炒時框**：**1m／5m／15m**（圖表 K 線、信號節奏、Momentum／AutoEarn）

## AutoEarn

Bots 頁可開關「自動幫你做單」：倉位美金、日虧 %、kill switch。  
**唔保證盈利／過去表現唔代表將來。** 預設紙上。

## 「100 個 AI」誠實說明

係 100 個**具名分析模組**投票成共識分數，**唔係**每秒打 100 次大模型。DeepSeek 係可選外掛。

## 幣安 API IP 白名單

1. Settings → **偵測 outbound IP**，或開 `GET /api/binance/outbound-ip`
2. 幣安 → API 管理 → 編輯 → 開啟 **IP 存取限制** → 貼上該 IP
3. 可將同一組 IP 寫入 `.env` 嘅 `BINANCE_WHITELIST_IPS`（逗號分隔）做備忘；唔會自動同步去幣安

## 點跑

```bash
cd services/engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8787

cd apps/web && npm i && npm run dev
```

瀏覽器開 `http://127.0.0.1:5173`。詳見英文 [README.md](./README.md) 同 [docs/PRODUCT.md](./docs/PRODUCT.md)。

## 風險

短炒可以好快蝕錢。本專案只供個人學習／模擬；唔係投資建議。AutoEarn **唔保證賺錢**。
