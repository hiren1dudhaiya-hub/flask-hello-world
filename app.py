import os, requests, time
from threading import Thread
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()

print(f"=== ENV CHECK ===")
print(f"BOT_TOKEN len: {len(BOT_TOKEN)}")
print(f"CHAT_ID: {CHAT_ID}")

def send_telegram(text):
    print(f"Sending TG to {CHAT_ID}...")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
        print(f"TG Response: {r.status_code} {r.text[:300]}")
    except Exception as e:
        print(f"TG Error: {e}")

def bot_polling():
    print("=== BOT POLLING STARTED ===")
    time.sleep(2)
    send_telegram("✅ *Delta20 Bot LIVE!* Bot start ho gaya!")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            resp = requests.get(url, timeout=35).json()
            if resp.get("ok"):
                for u in resp.get("result", []):
                    offset = u["update_id"] + 1
                    t = u.get("message", {}).get("text", "")
                    print(f"Got msg: {t}")
                    if t == "/start":
                        send_telegram("🤖 LIVE hai!")
        except Exception as e:
            print(f"Polling err: {e}")
            time.sleep(5)

@app.route('/')
def home():
    return f"Bot Live! Token:{len(BOT_TOKEN)} Chat:{CHAT_ID}"

Thread(target=bot_polling, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
