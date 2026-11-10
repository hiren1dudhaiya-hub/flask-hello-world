import os
import time
import requests
import threading
from flask import Flask
import pandas as pd

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # Tera Telegram Chat ID

COINS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "LTCUSDT", "BCHUSDT", "UNIUSDT", "XLMUSDT", "ETCUSDT",
    "FILUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "NEARUSDT"
]

app = Flask(__name__)

@app.route('/')
def home():
    return "Delta 20 Bot is LIVE - Auto 30 Min Active"

# --- TELEGRAM SEND ---
def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- BINANCE DATA ---
def get_klines(symbol, interval="1h", limit=100):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        df = pd.DataFrame(data, columns=['open_time','open','high','low','close','volume','close_time','qav','trades','taker_base','taker_quote','ignore'])
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    except:
        return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- CORE SCANNER (1.3x Vol + RSI) ---
def scan_market(manual=False):
    signals = []
    for symbol in COINS:
        df = get_klines(symbol)
        if df is None or len(df) < 50:
            continue
        
        df['rsi'] = calculate_rsi(df['close'])
        last = df.iloc[-1]
        prev_vol_avg = df['volume'].iloc[-21:-1].mean() # last 20 candle avg
        
        vol_ratio = last['volume'] / prev_vol_avg if prev_vol_avg > 0 else 0
        rsi_val = last['rsi']
        price = last['close']

        # CONDITION: Vol > 1.3x and RSI logic
        if vol_ratio >= 1.3:
            if rsi_val < 35:
                signals.append(f"🚀 **BUY: {symbol}** | Price: {price:.2f} | RSI: {rsi_val:.1f} | Vol: {vol_ratio:.2f}x")
            elif rsi_val > 70:
                signals.append(f"🔻 **SELL: {symbol}** | Price: {price:.2f} | RSI: {rsi_val:.1f} | Vol: {vol_ratio:.2f}x")

    if signals:
        msg = "🔥 **Delta 20 Signal (Binance Data)** 🔥\n\n" + "\n".join(signals)
        send_telegram(msg)
        return msg
    else:
        if manual:
            msg = "😴 **No Signal - Market Thanda Hai** (20 coin checked on Binance)"
            send_telegram(msg)
            return msg
        return None

# --- TELEGRAM COMMAND LISTENER ---
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
                    send_telegram("🔍 Scan Start (Real 1.3x Vol - Binance)...")
                    result = scan_market(manual=True)
                if "/backtest" in text:
                    send_telegram("Backtest feature coming soon in this version")
            time.sleep(2)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

# --- AUTO 30 MIN LOOP ---
def auto_scan_loop():
    time.sleep(20) # Bot start ke 20 sec baad pehla scan
    while True:
        print("Auto 30 Min Scan Running...")
        scan_market(manual=False) # Signal hoga to hi message jayega
        time.sleep(1800) # 30 min = 1800 sec

# Start Threads
threading.Thread(target=telegram_polling, daemon=True).start()
threading.Thread(target=auto_scan_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
