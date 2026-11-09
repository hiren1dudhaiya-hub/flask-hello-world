import threading, time, requests, os
from flask import Flask

BOT = "8819864573:AAEE_DHr1nmwVBwI2A38cnYJTGAOF1aHq10"
CHAT = "7086505670"
app = Flask(__name__)

def tg(m):
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id": CHAT, "text": m}, timeout=15)
        print(f"TG: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

def bot_polling():
    last_id = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{BOT}/getUpdates?offset={last_id+1}&timeout=10", timeout=15).json()
            for upd in r.get("result", []):
                last_id = upd["update_id"]
                msg = upd.get("message", {}).get("text", "")
                if "/start" in msg:
                    tg("✅ Delta20 Bot ACTIVE!\n\nBot: @Delta20rajkot_bot\nStatus: Running on Render\nYour ID: 7086505670\n\nAb se alerts yahin ayenge!")
        except:
            pass
        time.sleep(3)

def scan():
    tg("✅ Delta20 Bot FINAL LIVE! ID:7086505670")
    while True:
        time.sleep(60)

@app.route('/')
def home():
    return "Delta20 Bot LIVE!"

threading.Thread(target=scan, daemon=True).start()
threading.Thread(target=bot_polling, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
