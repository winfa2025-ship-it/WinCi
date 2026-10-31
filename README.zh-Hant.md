# WinCi（個人短炒 App）

海琋自用加密貨幣短炒儀表板。

## 功能

- 深色交易 UI（PWA）：行情、圖表 stub、下單（數量＋價錢）、機械人／**AutoEarn**、**100 信號板**、持倉、設定
- **電郵＋Google 登入**（本機 JWT；未設 `GOOGLE_CLIENT_ID` 可用 Demo Google）
- 預設 **紙上交易**；可選連幣安（v0.1.x LIVE 為 stub）
- **幣安 IP 白名單**備忘＋偵測引擎對外 IP
- 最低名義 **1 美金**；倉位上限；日虧 kill-switch
- 可選 **DeepSeek** AI 短評／信號微調；冇 key 紙上照常跑
- **連線燈**：綠＝已連接，紅＝未設定（Auth／Binance／DeepSeek／Bot）

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
