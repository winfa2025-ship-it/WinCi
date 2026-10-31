# WinCi — Product Design

**WinCi**（Win + Ci 短炒）係個人用加密貨幣短炒儀表板：紙上／實盤雙模式、機械人自動買賣、100 個全球信號分析模組共識評分、幣安現貨連接。

> 個人自用。預設 **PAPER**。LIVE 需自備 Binance API Key（唔好 commit）。

## Screens (MVP)

| Screen | Purpose |
|--------|---------|
| **Markets** | 交易對列表、24h 漲跌、即時價（紙上模擬 tick 或幣安） |
| **Chart** | K 線 stub（MVP 用簡易 sparkline；v2 接 TradingView widget） |
| **Order** | 限價／市價買入賣出：數量 + 價錢；最低名義 $1 USD |
| **Bots** | Momentum + **AutoEarn**：啟停、倉位美金、日虧 %、kill-switch；免責「唔保證盈利」 |
| **Login** | 電郵註冊／登入、Google（或 Demo Google）、訪客紙上 |
| **Signals** | 100 個具名分析器分數板 + 共識分數 |
| **Portfolio** | 持倉、未實現盈虧、成交紀錄、名義金額 |
| **Settings** | paper/live、帳號、DeepSeek、幣安 IP 白名單、**連線燈**（綠／紅） |

## 「100 AI」定義（誠實）

唔係每 tick 打 100 次 LLM。係 **100 個具名信號分析器**（技術指標、資金費率、未平倉、盤口失衡、新聞關鍵字、BTC 相關等）各自產出 -100…+100 分數，再投票成 **consensus score**。

分類（各約 10–15 個 stub）：
1. Trend / MA / EMA / MACD / ADX
2. Momentum / RSI / Stochastic / CCI
3. Volatility / ATR / Bollinger / Keltner
4. Volume / OBV / VWAP / CVD
5. Order book imbalance / spread / depth
6. Funding / OI / liquidations (perp-aware stubs)
7. BTC / ETH correlation & lead-lag
8. Cross-exchange premium stubs
9. News / keyword sentiment stubs
10. Session / calendar / volatility regime

MVP：全部以 **deterministic mock** 依 symbol+timestamp 種子產生；介面同加權共識已接好，之後可逐個換成真數據。

## Bots

MVP：**Simple Momentum** — 共識分數 > 閾值買、低於閾值賣；遵守 max position、daily loss kill-switch、min notional $1。

v2：多策略（mean-reversion、grid、DCA）、多交易對、回測。

## Binance scopes

- Spot read + trade（LIVE）
- 唔要 withdraw 權限
- Keys 只放 `.env` / 本機環境變數

## Risk controls

- `MIN_NOTIONAL_USD=1`
- `MAX_POSITION_USD`（預設 500 paper）
- `DAILY_LOSS_LIMIT_USD`（預設 50；觸發停所有 bot）
- Paper 與 Live 嚴格隔離帳本

## Roadmap

| Phase | Scope |
|-------|--------|
| **v0.1.1** | Paper + momentum + AutoEarn、email/Google auth、Binance IP whitelist helper、connection dots、DeepSeek optional |
| **v0.2** | 真 Binance spot via ccxt、真實 ticker、成交同步 |
| **v0.3** | 真指標（TA-Lib / pandas-ta）、Funding/OI、新聞 RSS |
| **v1.0** | 回測、多 bot、告警、手機 PWA 完善 |

## Non-goals (MVP)

- 合約／槓桿自動交易
- 提幣
- 託管他人資金
- 投資建議／保證回報

## DeepSeek AI plug-in (optional)

- Base URL: `https://api.deepseek.com`
- Env: `DEEPSEEK_API_KEY` (never commit)
- Settings UI: paste key for session, or use `.env`
- Features:
  - Short-trade commentary (HK Traditional Chinese + English line)
  - Optional signal boost (−10…+10) added to consensus
- **Paper mode works without the key** (stub commentary)
- Not financial advice; personal use only


## Auth (v0.1.1)

- Email/password → SQLite + JWT（`JWT_SECRET`）
- Google Identity：有 `GOOGLE_CLIENT_ID` 驗 ID token；否則 Demo Google
- Endpoints: `/auth/register` `/auth/login` `/auth/google` `/auth/me`

## AutoEarn (v0.1.1)

Opt-in bot，延伸 momentum。參數：position size USD、max daily loss %、kill switch。  
**唔保證盈利／過去表現唔代表將來。** 預設 paper。

## Binance IP whitelist

- `.env` `BINANCE_WHITELIST_IPS`（逗號分隔）＝備忘
- `GET /api/binance/outbound-ip`（或 `/binance/outbound-ip`）偵測引擎對外 IP，貼去幣安 API 管理 → IP 存取限制

## Connection indicators

Header + Settings：Auth / Binance / DeepSeek / Bot — **綠＝已連接，紅＝未設定／停**。
