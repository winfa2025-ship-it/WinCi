# WinCi（個人短炒 App）

海琋自用加密貨幣短炒儀表板。

## 功能

- 深色交易 UI（PWA）：行情、圖表 stub、下單（數量＋價錢）、機械人、**100 信號板**、持倉、設定
- 預設 **紙上交易**；可選連幣安（v0.1 LIVE 為 stub）
- 最低名義 **1 美金**；倉位上限；日虧 kill-switch
- 可選 **DeepSeek** AI 短評／信號微調（`https://api.deepseek.com`）；冇 key 紙上照常跑

## 「100 個 AI」誠實說明

係 100 個**具名分析模組**投票成共識分數，**唔係**每秒打 100 次大模型。DeepSeek 係可選外掛。

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

短炒可以好快蝕錢。本專案只供個人學習／模擬；唔係投資建議。
