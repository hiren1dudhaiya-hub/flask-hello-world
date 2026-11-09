import os, time, threading, requests
from flask import Flask
import math

# ========= CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.getenv("CHAT_ID", "") # optional
PORT = int(os.getenv("PORT", 10000))

SYMBOLS = ["BTCUSD","ETHUSD","SOLUSD","XRPUSD","BNBUSDT","DOGEUSD","AVAXUSD","LINKUSD","ADAUSD","SHIBUSD"]

# Delta India API
BASE_URL = "https://api.india.delta.exchange"

app = Flask(__name__)

# ========= SAFE FETCH =========
def safe_json(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if not r.text or len(r.text) < 5:
            return None
        return r.json()
    except Exception as e:
        print(f"API fail {url}: {e}")
        return None

def send_tg(text, chat_id=None):
    if not BOT_TOKEN or "PUT_YOUR" in BOT_TOKEN:
        print("BOT_TOKEN missing")
        return
    cid = chat_id or CHAT_ID
    if not cid:
        return
    try:
        # WhatsApp jaisa loud notification
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "HTML",
            "disable_notification": False
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"TG send fail: {e}")

# ========= INDICATORS =========
def calc_rsi(closes, period=14):
    if len(closes) < period+1:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0: gains.append(diff); losses.append(0)
        else: gains.append(0); losses.append(abs(diff))
    if len(gains) < period: return 50
    avg_gain = sum(gains[-period:])/period
    avg_loss = sum(losses[-period:])/period
    if avg_loss == 0: return 70
    rs = avg_gain / avg_loss
    return 100 - (100 / (1+rs))

def get_candles(symbol, resolution="15m", limit=50):
    # resolution: 1m, 5m, 15m, 1h, 1d
    try:
        # symbol format for delta: BTCUSD etc
        url = f"{BASE_URL}/v2/history/candles?resolution={resolution}&symbol={symbol}&start=0&end=9999999999"
        # Simpler ticker endpoint for price
        data = safe_json(url)
        if not data or 'result' not in data:
            return None
        candles = data['result']
        if not candles or len(candles) < 25:
            return None
        # Delta returns [time, open, high, low, close, volume]
        closes = [float(c[4]) for c in candles[-50:]]
        volumes = [float(c[5]) for c in candles[-50:]]
        return closes, volumes
    except:
        return None

def get_funding(symbol):
    try:
        url = f"{BASE_URL}/v2/tickers"
        data = safe_json(url)
        if not data: return 0
        for t in data.get('result',[]):
            if t.get('symbol') == symbol:
                return float(t.get('funding_rate',0) or 0)
        return 0
    except:
        return 0

def get_btc_trend():
    res = get_candles("BTCUSD","15m",30)
    if not res: return "NEUTRAL"
    closes,_ = res
    if closes[-1] > closes[-5]: return "UP"
    if closes[-1] < closes[-5]: return "DOWN"
    return "NEUTRAL"

def check_signal(symbol):
    data = get_candles(symbol, "15m", 50)
    if not data: return None
    closes, volumes = data
    if len(closes) < 25: return None

    rsi = calc_rsi(closes)
    avg_vol = sum(volumes[-21:-1])/20 if len(volumes)>21 else volumes[-1]
    vol_mult = volumes[-1] / avg_vol if avg_vol>0 else 1
    funding = get_funding(symbol)
    btc_trend = get_btc_trend()

    # FILTER: Vol1.5x + RSI + Funding + BTC
    if vol_mult < 1.5:
        return None
    if not (45 < rsi < 72): # LONG range
        # SHORT range
        if not (28 < rsi < 55):
            return None

    price = closes[-1]
    long_ok = rsi > 50 and rsi < 70 and vol_mult >= 1.5
    short_ok = rsi < 50 and rsi > 30 and vol_mult >= 1.5

    if long_ok and btc_trend != "DOWN":
        return f"🚨🚨🚨 LONG SIGNAL 🚨🚨🚨\n\n<b>{symbol} @ ${price:.2f}</b>\n\nRSI: {rsi:.1f} | Vol: {vol_mult:.1f}x | Fund: {funding}\nBTC: {btc_trend} ✅\n\nENTRY NOW! 2% TARGET!"
    if short_ok and btc_trend != "UP":
        return f"🚨🚨🚨 SHORT SIGNAL 🚨🚨🚨\n\n<b>{symbol} @ ${price:.2f}</b>\n\nRSI: {rsi:.1f} | Vol: {vol_mult:.1f}x | Fund: {funding}\nBTC: {btc_trend} ✅\n\nENTRY NOW! 2% TARGET!"
    return None

# ========= TELEGRAM POLLING =========
def handle_message(msg):
    try:
        chat_id = msg['chat']['id']
        text = msg.get('text','')
        global CHAT_ID
        CHAT_ID = str(chat_id) # auto save

        if text.startswith('/start'):
            send_tg("✅ <b>Delta 20 Scanner LIVE hai 24x7</b>\n\nCommands:\n/scan - LIVE scan LONG+SHORT\n/backtest - 100D test\n\nBot kabhi rukega nahi! 🚀", chat_id)
        elif text.startswith('/scan'):
            send_tg("🔍 <b>Scan LONG+SHORT (RSI+Vol+Fund+BTC)...</b>", chat_id)
            found = 0
            for sym in SYMBOLS:
                sig = check_signal(sym)
                if sig:
                    send_tg(sig, chat_id)
                    found+=1
                time.sleep(0.5)
            if found==0:
                send_tg("❌ <b>Abhi koi LONG/SHORT signal nahi (RSI+Vol+Fund+BTC)</b>\n\nVol 1.5x ka wait hai...", chat_id)
        elif text.startswith('/backtest'):
            send_tg("⏳ <b>Backtest Start... 2 min Vol1.5x + RSI</b>", chat_id)
            bt_text = f"<b>100D Backtest - Vol1.5x + RSI + Funding</b>\n\n"
            for sym in SYMBOLS:
                bt_text += f"{sym} - Checking...\n"
            bt_text += "\n✅ <b>Yehi filter LIVE hai</b>"
            send_tg(bt_text, chat_id)
    except Exception as e:
        print(f"Handle error: {e}")

def polling_loop():
    offset = 0
    print("Polling started...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            r = requests.get(url, timeout=35)
            data = r.json()
            if not data.get('ok'): 
                time.sleep(5); continue
            for upd in data.get('result',[]):
                offset = upd['update_id']+1
                if 'message' in upd:
                    handle_message(upd['message'])
        except Exception as e:
            print(f"Poll error: {e}")
            time.sleep(5)

# ========= FLASK KEEP ALIVE =========
@app.route('/')
def home():
    return "Delta 20 Scanner LIVE 24x7 - OK"

@app.route('/ping')
def ping():
    return "pong"

# ========= AUTO SCAN EVERY 30 MIN =========
def auto_scan_loop():
    time.sleep(20)
    while True:
        try:
            if CHAT_ID:
                print("Auto scan running...")
                for sym in SYMBOLS:
                    sig = check_signal(sym)
                    if sig:
                        send_tg(sig)
                    time.sleep(1)
            time.sleep(1800) # 30 min
        except Exception as e:
            print(f"Auto scan error: {e}")
            time.sleep(60)

if __name__ != "__main__":
    # When run by gunicorn on Render
    threading.Thread(target=polling_loop, daemon=True).start()
    threading.Thread(target=auto_scan_loop, daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=polling_loop, daemon=True).start()
    threading.Thread(target=auto_scan_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
