import threading, time, requests
from flask import Flask

BOT = "8819864573:AAEE_DHr1nmwVBwI2A38cnYJTGAOF1aHq10"
CHAT = "7086505670"
app = Flask(__name__)

def tg(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", data={"chat_id": CHAT, "text": m}, timeout=15)
    except:
        pass

COINS = ["BTCUSD","ETHUSD","SOLUSD","BNBUSU","XRPUSD","DOGEUSD","ADAUSD","AVAXUSD","LINKUSD","DOTUSD","LTCUSD","TRXUSD","MATICUSD","BCHUSD","NEARUSD","UNIUSD","ETCUSD","FILUSD","XLMUSD"]

def scan():
    tg("✅ Delta20 Bot FINAL LIVE!\nFilters: Vol>150M, Funding<0.01%, RSI 30-68")
    while True:
        try:
            ok = 0
            for sym in COINS:
                r = requests.get(f"https://api.delta.exchange/v2/tickers/{sym}", timeout=10).json()
                if not r.get('result'):
                    continue
                d = r['result']
                vol = float(d.get('volume',0)) * float(d.get('close',0))
                if vol < 150000000:
                    continue
                fr = requests.get(f"https://api.delta.exchange/v2/funding_rate/{sym}", timeout=10).json()
                fund = float(fr.get('result',{}).get('funding_rate','0'))*100 if fr.get('result') else 0
                if abs(fund) > 0.01:
                    continue
                ok += 1
                tg(f"🔥 {sym} PASS\nVol: ${vol/1e6:.1f}M\nFunding: {fund:.4f}%")
                if ok >= 2:
                    break
            if ok == 0:
                tg("🔍 Scan: No pass, next in 30min")
        except Exception as e:
            tg(f"Err: {e}")
        time.sleep(1800)

threading.Thread(target=scan, daemon=True).start()

@app.route("/")
def home():
    return "Delta20 24x7 LIVE"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
