from flask import Flask
import threading
import time
import os
import requests

app = Flask(__name__)

# --- TERA TELEGRAM CONFIG (Yaha apna daal) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
CHAT_ID = os.environ.get("CHAT_ID", "PUT_YOUR_CHAT_ID_HERE")

def send_telegram(msg):
    try:
        if "PUT_YOUR" in BOT_TOKEN: return
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def delta_scanner_loop():
    print("Delta 20 Scanner Started...")
    send_telegram("✅ *Delta 20 Bot LIVE ho gaya hai - Render pe!*")
    while True:
        try:
            # Yaha tera asli scanning logic aayega
            # Example:
            # if condition: send_telegram("🚀 BUY SIGNAL...")
            print("Scanning...")
            time.sleep(60) # 1 min me check
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(10)

# Bot ko background me chalu karo
threading.Thread(target=delta_scanner_loop, daemon=True).start()

@app.route('/')
def home():
    return "LIVE 24x7 - OK - Delta 20 Scanner Running 🚀"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
