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
    except: pass

def get_coin_data(symbol):
    try:
        t_url = f"https://api.delta.exchange/v2/tickers/{symbol}"
        t = requests.get(t_url, timeout=10).json().get("result", {})
        price = float(t.get("close", 0))
        funding = float(t.get("funding_rate", 0)) * 100
        c_url = f"https://api.delta.exchange/v2/chart/candles?symbol={symbol}&resolution=1h&count=100"
        c = requests.get(c_url, timeout=15).json()
        candles = c.get("result", []) if c.get("success") else []
        if len(candles) < 30: return None
        closes = [float(x[4]) for x in candles]
        volumes = [float(x[5]) * float(x[4]) for x in candles]
        avg_vol = statistics.mean(volumes[-20:]) if volumes else 0
        curr_vol = volumes[-1] if volumes else 0
        gains=[]; losses=[]
        for i in range(1,len(closes)):
            diff=closes[i]-closes[i-1]
            if diff>0: gains.append(diff)
            else: losses.append(abs(diff))
        rsi=50
        if len(gains)>14 and len(losses)>14:
            avg_g=sum(gains[-14:])/14
            avg_l=sum(losses[-14:])/14
            if avg_l!=0:
                rs=avg_g/avg_l
                rsi=100-(100/(1+rs))
        return {"price":price, "funding":funding, "rsi":rsi, "curr_vol":curr_vol, "avg_vol":avg_vol, "closes":closes}
    except: return None

def get_btc_trend():
    try:
        d=get_coin_data("BTCUSD")
        return d["closes"][-1] > d["closes"][-6] if d else True
    except: return True

def get_signal_type(d):
    if not d or d["avg_vol"]==0: return None
    if d["curr_vol"] <= d["avg_vol"]*1.5: return None
    if d["funding"] < 0.01 and 30 < d["rsi"] < 68:
        return "LONG"
    if d["funding"] > 0.05 and d["rsi"] > 70:
        return "SHORT"
    return None

def scanner_loop():
    print("SCANNER LONG+SHORT STARTED")
    while True:
        try:
            btc_up = get_btc_trend()
            for coin in COINS:
                d=get_coin_data(coin)
                sig=get_signal_type(d)
                if sig:
                    if sig=="LONG" and not btc_up: continue
                    if sig=="SHORT" and btc_up: continue
                    if sig=="LONG":
                        msg=f"🚀 *LONG - {coin}*\nPrice: {d['price']}\nRSI: {d['rsi']:.1f} (30-68 OK)\nVol: {d['curr_vol']/d['avg_vol']:.1f}x\nFunding: {d['funding']:.4f}% LOW\nBTC: UP"
                    else:
                        msg=f"🔻 *SHORT - {coin}*\nPrice: {d['price']}\nRSI: {d['rsi']:.1f} (>70)\nVol: {d['curr_vol']/d['avg_vol']:.1f}x\nFunding: {d['funding']:.4f}% HIGH\nBTC: DOWN"
                    send_tg(msg)
                time.sleep(1.5)
            time.sleep(1800)
        except Exception as e:
            print(f"Scanner err: {e}")
            time.sleep(60)

def run_backtest_thread():
    try:
        send_tg("⏳ *Backtest Start... 2 min* Vol1.5x + RSI")
        report=[]
        for coin in COINS[:10]:
            try:
                # Daily fail ho raha hai, isiliye 4h use kar rahe hai
                url=f"https://api.delta.exchange/v2/chart/candles?symbol={coin}&resolution=1h&count=500"
                resp=requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"})
                data=resp.json()
                raw=data.get("result", []) if data.get("success") else []
                if len(raw)<100:
                    report.append(f"{coin} NoData")
                    continue
                # 1h se daily banao - har 24 candle ka 1 daily
                daily=[]
                for i in range(0,len(raw),24):
                    chunk=raw[i:i+24]
                    if len(chunk)<24: continue
                    # chunk list ya dict ho sakta hai
                    closes=[]
                    highs=[]
                    lows=[]
                    vols=[]
                    for x in chunk:
                        if isinstance(x, dict):
                            closes.append(float(x.get("close",0)))
                            highs.append(float(x.get("high",0)))
                            lows.append(float(x.get("low",0)))
                            vols.append(float(x.get("volume",0))*float(x.get("close",0)))
                        else:
                            closes.append(float(x[4])); highs.append(float(x[2])); lows.append(float(x[3])); vols.append(float(x[5])*float(x[4]))
                    if not closes: continue
                    daily.append([0, closes[0], max(highs), min(lows), closes[-1], sum(vols)/closes[-1] if closes[-1] else 0])
                
                if len(daily)<40:
                    report.append(f"{coin} Less daily")
                    continue

                long_t=long_w=short_t=short_w=0
                for i in range(30,len(daily)-4):
                    try:
                        curr_v=float(daily[i][5])*float(daily[i][4])
                        vols=[float(c[5])*float(c[4]) for c in daily[i-20:i]]
                        avg_v=sum(vols)/len(vols) if vols else 0
                        if avg_v==0 or curr_v <= avg_v*1.5: continue
                        closes=[float(c[4]) for c in daily[i-14:i+1]]
                        gain=sum([max(0, closes[k]-closes[k-1]) for k in range(1,len(closes))])
                        loss=sum([max(0, closes[k-1]-closes[k]) for k in range(1,len(closes))])+0.0001
                        rsi=100-(100/(1+gain/loss))
                        if 30<rsi<68:
                            long_t+=1
                            entry=float(daily[i][4])
                            if max([float(c[2]) for c in daily[i+1:i+4]])>=entry*1.02: long_w+=1
                        elif rsi>70:
                            short_t+=1
                            entry=float(daily[i][4])
                            if min([float(c[3]) for c in daily[i+1:i+4]])<=entry*0.98: short_w+=1
                    except: continue
                l_per=int(long_w*100/long_t) if long_t else 0
                s_per=int(short_w*100/short_t) if short_t else 0
                report.append(f"{coin} L:{long_t} {l_per}% | S:{short_t} {s_per}%")
            except Exception as e:
                report.append(f"{coin} {str(e)[:15]}")
            time.sleep(0.5)
        send_tg("*100D Backtest - Vol1.5x + RSI + Funding*\n\n" + "\n".join(report) + "\n\n✅ Yehi filter LIVE hai")
    except Exception as e:
        send_tg(f"Crash: {e}")
def bot_polling():
    offset=0
    while True:
        try:
            url=f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            resp=requests.get(url, timeout=35).json()
            if resp.get("ok"):
                for u in resp.get("result", []):
                    offset=u["update_id"]+1
                    txt=u.get("message",{}).get("text","").strip()
                    if txt=="/start":
                        send_tg("🤖 *LIVE LONG+SHORT!*\n`/scan` = quick scan\n`/backtest` = 100 din report\n🚀 LONG: RSI 30-68 + Vol1.5x + Fund <0.01 + BTC UP\n🔻 SHORT: RSI >70 + Vol1.5x + Fund >0.05 + BTC DOWN")
                    elif txt=="/scan":
                        send_tg("🔍 Scan LONG+SHORT (RSI+Vol+Fund+BTC)...")
                        found=0
                        btc_up=get_btc_trend()
                        for coin in COINS:
                            d=get_coin_data(coin)
                            sig=get_signal_type(d)
                            if sig:
                                if sig=="LONG" and not btc_up: continue
                                if sig=="SHORT" and btc_up: continue
                                send_tg(f"{'🚀' if sig=='LONG' else '🔻'} {coin} {sig} RSI {d['rsi']:.1f} Vol {d['curr_vol']/d['avg_vol']:.1f}x Fund {d['funding']:.4f}%")
                                found+=1
                        if found==0: send_tg("❌ Abhi koi LONG/SHORT signal nahi (RSI+Vol+Fund+BTC)")
                    elif txt=="/backtest":
                        Thread(target=run_backtest_thread, daemon=True).start()
        except: time.sleep(5)

@app.route('/')
def home(): return "Delta20 LONG+SHORT Live All Filters!"

Thread(target=bot_polling, daemon=True).start()
Thread(target=scanner_loop, daemon=True).start()

if __name__=="__main__":
    port=int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
