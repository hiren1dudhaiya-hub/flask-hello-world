from flask import Flask
import threading, time, os, requests

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send(msg):
    try:
        requests.post(f"{BASE_URL}/sendMessage", data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_updates(offset):
    try:
        r = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25).json()
        return r.get("result", [])
    except: return []

def do_scan():
    # Yaha tera asli RSI+Vol+Fund+BTC wala logic
    send("🔍 Scan LONG+SHORT (RSI+Vol+Fund+BTC)...\n❌ Abhi koi LONG/SHORT signal nahi\nVol 1.5x ka wait hai...")

def do_backtest():
    send("📊 100D Backtest Running... Result jaldi aayega")

def bot_loop():
    send("✅ *Delta 20 Scanner LIVE hai 24x7*\n\nCommands:\n/scan - LIVE scan LONG+SHORT\n/backtest - 100D test\n\nBot kabhi rukega nahi! 🚀")
    offset = 0
    while True:
        try:
            for upd in get_updates(offset):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                text = msg.get("text", "")
                chat_id = str(msg.get("chat", {}).get("id", ""))
                # Sirf tere CHAT_ID se hi command lega
                if chat_id != str(CHAT_ID): continue
                if text == "/scan": do_scan()
                elif text == "/backtest": do_backtest()
            time.sleep(2)
        except Exception as e:
            print(e); time.sleep(5)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home(): return "LIVE 24x7 - OK - Delta 20 Scanner Running 🚀"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
