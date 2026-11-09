import os, requests, time
from threading import Thread
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()

print(f"=== ENV CHECK ===")
print(f"BOT_TOKEN len: {len(BOT_TOKEN)} value start: {BOT_TOKEN[:6]}...")
print(f"CHAT_ID len: {len(CHAT_ID)} value: {CHAT_ID}")

def send_telegram(text):
    print(f"Attempting to send TG to {CHAT_ID}...")
    if not BOT_TOKEN or not CHAT_ID:
        print("ENV Missing! Cannot send")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        r = requests.post(url, json=payload, timeout=15)
        print(f"TG Response: {r.status_code} - {r.text[:200]}")
        return r.text
    except Exception as e:
        print(f"TG Error Exception: {e}")
        import traceback
        traceback.print_exc()

def bot_polling():
    print("=== BOT POLLING STARTED ===")
    time.sleep(3)
    send_telegram("✅ *Delta20 Bot FINAL LIVE!*\n\nBot Render pe successfully start ho gaya!\n`/start` bhejo")
    offset = 0
    print("Starting getUpdates loop...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            resp = requests.get(url, timeout=35).json()
            if resp.get("ok"):
                for update in resp.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    print(f"Received: {text}")
                    if text == "/start":
                        send_telegram("🤖 *Delta 20 Scanner LIVE hai!*\n\nAb kaam kar raha hai.")
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
        time.sleep(1)

@app.route('/')
def home():
    return f"Bot Live! Token len {len(BOT_TOKEN)} Chat {CHAT_ID}"

Thread(target=bot_polling, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
