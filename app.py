import os
import requests
import time
from threading import Thread
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("ENV Missing!")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        print(f"TG Sent: {r.json()}")
    except Exception as e:
        print(f"TG Error: {e}")

def bot_polling():
    print("Bot polling started...")
    offset = 0
    # Startup message
    send_telegram("✅ *Delta20 Bot FINAL LIVE!*\nRender pe successfully start ho gaya hai!\n\n`/start` bhejo test karne ke liye.")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            resp = requests.get(url, timeout=35).json()
            if resp.get("ok"):
                for update in resp.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id"))
                    text = msg.get("text", "")
                    
                    if text == "/start":
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        requests.post(send_url, json={
                            "chat_id": chat_id,
                            "text": "🤖 *Delta 20 Scanner LIVE hai!*\n\nBot kaam kar raha hai.\nScanner active hai.",
                            "parse_mode": "Markdown"
                        })
            time.sleep(1)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

@app.route('/')
def home():
    return "Delta20 Bot is Live!"

# Start bot in background thread
Thread(target=bot_polling, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
