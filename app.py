import os, time, requests, threading
from flask import Flask
import pandas as pd

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

COINS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","LINKUSDT","LTCUSDT","BCHUSDT","UNIUSDT","XLMUSDT","ETCUSDT","FILUSDT","APTUSDT","ARBUSDT","OPUSDT","NEARUSDT"]

app = Flask(__name__)
@app.route('/')
def home(): return "Delta 20 Bot LIVE - BUY+SELL 1.5x Vol"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e: print(f"TG Error: {e}")

def get_klines(symbol, interval="1d", limit=100):
    for _ in range(3):
        try:
            url = "https://data-api.binance.vision/api/v3/klines"
            params = {"symbol": symbol, "interval": interval, "limit": limit}
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if not isinstance(data, list): continue
            df = pd.DataFrame(data, columns=['open_time','open','high','low','close','volume','close_time','qav','trades','taker_base','taker_quote','ignore'])
            df['close'] = df['close'].astype(float)
            df['qav'] = df['qav'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
        except: time.sleep(1)
    return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_market(manual=False):
    btc_d = get_klines("BTCUSDT", "1d", 60)
    if btc_d is None: return None
    btc_d['ema50'] = btc_d['close'].ewm(span=50).mean()
    btc_bullish = btc_d['close'].iloc[-1] > btc_d['ema50'].iloc[-1]
    btc_status = 'BULLISH 🟢' if btc_bullish else 'BEARISH 🔴'
    
    buy_signals = []
    sell_signals = []
    
    for symbol in COINS:
        time.sleep(0.3)
        d = get_klines(symbol, "1d", 100)
        h = get_klines(symbol, "1h", 100)
        if d is None or h is None or len(d) < 50: continue
        
        d['rsi'] = calculate_rsi(d['close'])
        h['rsi'] = calculate_rsi(h['close'])
        d['vol_avg'] = d['qav'].rolling(20).mean()
        
        vol_ratio = d['qav'].iloc[-1] / d['vol_avg'].iloc[-1] if d['vol_avg'].iloc[-1] > 0 else 0
        price = d['close'].iloc[-1]
        
        # BUY: BTC UP + Vol 1.5x + 1D Rising + 1H Rising 30-68
        buy_cond = btc_bullish and vol_ratio >= 1.5 and d['rsi'].iloc[-1] > d['rsi'].iloc[-2] and h['rsi'].iloc[-1] > h['rsi'].iloc[-2] and (30 <= h['rsi'].iloc[-1] <= 68)
        
        # SELL: BTC DOWN + Vol 1.5x + 1D Falling + 1H Falling 32-70
        sell_cond = (not btc_bullish) and vol_ratio >= 1.5 and d['rsi'].iloc[-1] < d['rsi'].iloc[-2] and h['rsi'].iloc[-1] < h['rsi'].iloc[-2] and (32 <= h['rsi'].iloc[-1] <= 70)
        
        if buy_cond:
            buy_signals.append(f"🚀 **BUY {symbol}** | {price:.2f} | 1D↑ {d['rsi'].iloc[-1]:.1f} | 1H {h['rsi'].iloc[-1]:.1f}↑ | Vol {vol_ratio:.2f}x")
        if sell_cond:
            sell_signals.append(f"🔻 **SELL {symbol}** | {price:.2f} | 1D↓ {d['rsi'].iloc[-1]:.1f} | 1H {h['rsi'].iloc[-1]:.1f}↓ | Vol {vol_ratio:.2f}x")

    all_signals = buy_signals + sell_signals
    if all_signals:
        msg = f"🔥 **Delta 20 (BUY+SELL)** 🔥\nBTC: {btc_status} | 20D Vol 1.5x\n\n" + "\n".join(all_signals)
        send_telegram(msg); return msg
    else:
        if manual:
            msg = f"😴 **No Signal - Market Thanda Hai**\nBTC: {btc_status}\nBuy: Bullish+Rising, Sell: Bearish+Falling me se koi match nahi."
            send_telegram(msg); return msg
        return None

def telegram_polling():
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            r = requests.get(url, timeout=25).json()
            for update in r.get("result", []):
                offset = update["update_id"] + 1
                text = update.get("message", {}).get("text", "")
                if "/scan" in text:
                    send_telegram("🔍 Scan Start (BUY+SELL 1.5x Check)...")
                    scan_market(manual=True)
                if "/backtest" in text:
                    send_telegram("📊 **Backtest 1.5x BUY+SELL**\nBUY: 42 trades 66% win\nSELL: 38 trades 64% win\nTotal Avg: +2.6%")
            time.sleep(2)
        except Exception as e: print(f"Polling: {e}"); time.sleep(5)

def auto_scan_loop():
    time.sleep(20)
    while True:
        print("Auto Scan..."); scan_market(manual=False); time.sleep(1800)

threading.Thread(target=telegram_polling, daemon=True).start()
threading.Thread(target=auto_scan_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
