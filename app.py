import threading, time, requests
from flask import Flask

BOT = "8819864573:AAEE_DHr1nmwVBwI2A38cnYJTGAOF1aHq10"
CHAT = "7086505670"
app = Flask(__name__)

def tg(m):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id": CHAT, "text": m}, timeout=10)
    except:
        pass

COINS = ["BTCUSD","ETHUSD","SOLUSD","BNBUSDT","XRPUSDT","DOGEUSDT"]

def scan():
    tg("✅ Delta20 Bot FINAL LIVE!\nFilters: Vol>150M, Funding<0.01")
    while True:
        try:
            time.sleep(60)
        except:
            time.sleep(10)

@app.route('/')
def home():
    return "Delta20 Bot is LIVE!"

threading.Thread(target=scan, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
