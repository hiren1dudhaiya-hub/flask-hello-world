import threading, time, requests, os
from flask import Flask

BOT = "8819864573:AAEE_DHr1nmwVBwI2A38cnYJTGAOF1aHq10"
CHAT = "7086505670"
app = Flask(__name__)

def tg(m):
    try:
        url = f"https://api.telegram.org/bot{BOT}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT, "text": m}, timeout=15)
        print(f"TG: {r.text}")
    except Exception as e:
        print(f"TG Error: {e}")

def scan():
    print("Scan thread started")
    tg("✅ Delta20 Bot FINAL LIVE!\nBot: @Delta20rajkot_bot\nID: 7086505670\nStatus: Working")
    while True:
        time.sleep(60)

@app.route('/')
def home():
    return "Delta20 Bot LIVE! @Delta20rajkot_bot"

threading.Thread(target=scan, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
