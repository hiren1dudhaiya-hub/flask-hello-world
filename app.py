import os, requests, time, statistics
from threading import Thread
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()

COINS = ["BTCUSD","ETHUSD","SOLUSD","XRPUSD","BNBUSD","DOGEUSD","AVAXUSD","LINKUSD","ADAUSD","SHIBUSD","MATICUSD","DOTUSD","LTCUSD","TRXUSD","ETCUSD","UNIUSD","ATOMUSD","FILUSD","NEARUSD","APTUSD"]

def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except:
        pass

def get_coin_data(symbol):
    try:
        t_url = f"https://api.delta.exchange/v2/tickers/{symbol}"
        t = requests.get(t_url, timeout=10).json().get("result", {})
        price = float(t.get("close", 0))
        funding = float(t.get("funding_rate", 0)) * 100
        c_url = f"https://api.delta.exchange/v2/chart/candles?symbol={symbol}&resolution=1h&count=100"
        c = requests.get(c_url, timeout=15).json()
        candles = c.get("result", []) if c.get("success") else []
        if len(candles) < 30:
            return None
        closes = [float(x[4]) for x in candles]
        volumes = [float(x[5]) * float(x[4]) for x in candles]
        avg_vol = statistics.mean(volumes[-20:]) if volumes else 0
        curr_vol = volumes[-1] if volumes else 0
        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        rsi = 50
        if len(gains) > 14 and len(losses) > 14:
            avg_g = sum(gains[-14:]) / 14
            avg_l = sum(losses[-14:]) / 14
            if avg_l != 0:
                rs = avg_g / avg_l
                rsi = 100 - (100 / (1 + rs))
        return {"price": price, "funding": funding, "rsi": rsi, "curr_vol": curr_vol, "avg_vol": avg_vol, "closes": closes}
    except:
        return None

def get_btc_trend():
    try:
        d = get_coin_data("BTCUSD")
        return d["closes"][-1] > d["closes"][-6] if d else True
    except:
        return True

def is_signal(d):
    if not d:
        return False
    smart_vol_ok = d["curr_vol"] > (d["avg_vol"] * 1.5) if d["avg_vol"] > 0 else False
    return smart_vol_ok and d["funding"] < 0.01 and 30 < d["rsi"] < 68

def scanner_loop():
    print("SCANNER STARTED - SMART VOL")
    while True:
        try:
            btc_up = get_btc_trend()
            if btc_up:
                for coin in COINS:
                    d = get_coin_data(coin)
                    if d and is_signal(d):
                        msg = f"🚀 *{coin}*\nPrice: {d['price']}\nRSI: {d['rsi']:.1f}\nVol: {d['curr_vol']/1e6:.1f}M (Avg {d['avg_vol']/1e6:.1f}M) {d['curr_vol']/d['avg_vol']:.1f}x\nFunding: {d['funding']:.4f}%\nBTC: UP"
                        send_tg(msg)
                    time.sleep(1.5)
            time.sleep(1800)
        except Exception as e:
            print(f"Scanner err: {e}")
            time.sleep(60)

def run_backtest_thread():
    try:
        send_tg("⏳ *Backtest Start... 20 coins x 100 days, 8-10 min lagega*")
        report = []
        for coin in COINS:
            try:
                url = f"https://api.delta.exchange/v2/chart/candles?symbol={coin}&resolution=1d&count=105"
                r = requests.get(url, timeout=15).json()
                candles = r.get("result", []) if r.get("success") else []
                if len(candles) < 50:
                    continue
                trades = 0
                wins = 0
                for i in range(20, len(candles)-3):
                    vols = [float(c[5]) * float(c[4]) for c in candles[i-20:i]]
                    avg_v = statistics.mean(vols) if vols else 0
                    curr_v = float(candles[i][5]) * float(candles[i][4])
                    closes = [float(c[4]) for c in candles[i-14:i+1]]
                    gains = []
                    losses = []
                    for k in range(1, len(closes)):
                        diff = closes[k] - closes[k-1]
                        if diff > 0:
                            gains.append(diff)
                        else:
                            losses.append(abs(diff))
                    rsi = 50
                    if gains and losses and sum(losses) != 0:
                        avg_g = sum(gains) / len(gains)
                        avg_l = sum(losses) / len(losses)
                        rs = avg_g / avg_l
                        rsi = 100 - (100 / (1 + rs))
                    if curr_v > avg_v * 1.5 and 30 < rsi < 68:
                        trades += 1
                        entry = float(candles[i][4])
                        future = max([float(c[2]) for c in candles[i+1:i+4]])
                        if future >= entry * 1.02:
                            wins += 1
                if trades > 0:
                    report.append(f"{coin}: {trades}T Win {wins*100//trades if trades else 0}%")
                time.sleep(0.5)
            except:
                pass
        final_msg = "*100D Backtest - Smart 1.5x Vol*\n\n" + "\n".join(report)
        send_tg(final_msg)
    except Exception as e:
        send_tg(f"Backtest error: {e}")

def bot_polling():
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            resp = requests.get(url, timeout=35).json()
            if resp.get("ok"):
                for u in resp.get("result", []):
                    offset = u["update_id"] + 1
                    txt = u.get("message", {}).get("text", "").strip()
                    if txt == "/start":
                        send_tg("🤖 LIVE hai! `/scan` = quick scan\n`/backtest` = 100 din report\nAuto scan har 30 min")
                    elif txt == "/scan":
                        send_tg("🔍 Scan kar raha hu...")
                        found = 0
                        for coin in COINS:
                            d = get_coin_data(coin)
                            if d and is_signal(d):
                                send_tg(f"✅ {coin} RSI {d['rsi']:.1f} Vol {d['curr_vol']/d['avg_vol']:.1f}x")
                                found += 1
                        if found == 0:
                            send_tg("❌ Abhi Smart Vol filter me koi signal nahi")
                    elif txt == "/backtest":
                        Thread(target=run_backtest_thread, daemon=True).start()
        except:
            time.sleep(5)

@app.route('/')
def home():
    return "Delta20 Stable!"

Thread(target=bot_polling, daemon=True).start()
Thread(target=scanner_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
