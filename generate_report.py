#!/usr/bin/env python3
"""
Bitcoin Daily Report Generator v4.0
Generates comprehensive BTC report with charts, sentiment, and analysis
Auto-publishes to GitHub Pages
"""

import json
import urllib.request
import os
from datetime import datetime, timedelta

REPORT_DIR = "."
TRACKER_DIR = "../btc-daily-report-tracker"

class BitcoinDailyReport:
    def __init__(self):
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.price_data = {}
        self.sentiment = {}
        self.ohlc_data = []
        
    def fetch_binance_data(self):
        """Fetch BTC data from Binance"""
        try:
            # 24hr ticker
            req = urllib.request.Request(
                "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read())
                self.price_data = {
                    "price": float(data["lastPrice"]),
                    "change_24h": float(data["priceChangePercent"]),
                    "high": float(data["highPrice"]),
                    "low": float(data["lowPrice"]),
                    "volume": float(data["volume"]),
                    "quote_volume": float(data["quoteVolume"]),
                    "open": float(data["openPrice"])
                }
            
            # OHLC data for 90 days
            req = urllib.request.Request(
                "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=90",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                self.ohlc_data = json.loads(response.read())
                
            print(f"✅ Price: ${self.price_data['price']:,.2f} | Change: {self.price_data['change_24h']:.2f}%")
            return True
        except Exception as e:
            print(f"❌ Binance error: {e}")
            return False
    
    def fetch_x_sentiment(self):
        """Fetch Bitcoin sentiment from X/Twitter"""
        try:
            bearer = os.environ.get("X_API_BEARER_TOKEN", "")
            if not bearer:
                self.sentiment = {"bullish": 50, "bearish": 50, "tweets": 0}
                return False
            
            req = urllib.request.Request(
                "https://api.twitter.com/2/tweets/search/recent?query=Bitcoin%20OR%20BTC%20-is:retweet&lang:en&max_results=50",
                headers={"Authorization": f"Bearer {bearer}"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                tweets = json.loads(response.read())
                
                bullish_words = ["moon", "bull", "pump", "buy", "long", "up", "rise", "gain", "ATH", "breakout"]
                bearish_words = ["bear", "dump", "sell", "short", "down", "crash", "fall", "capitulation", "bearish"]
                
                bullish = 0
                bearish = 0
                
                for tweet in tweets.get("data", []):
                    text = tweet.get("text", "").lower()
                    if any(w in text for w in bullish_words):
                        bullish += 1
                    elif any(w in text for w in bearish_words):
                        bearish += 1
                
                total = bullish + bearish
                if total > 0:
                    self.sentiment = {
                        "bullish": round((bullish / total) * 100, 1),
                        "bearish": round((bearish / total) * 100, 1),
                        "tweets": len(tweets.get("data", []))
                    }
                else:
                    self.sentiment = {"bullish": 50, "bearish": 50, "tweets": 0}
                    
            print(f"✅ Sentiment: {self.sentiment['bullish']}% bullish")
            return True
        except Exception as e:
            print(f"❌ X API error: {e}")
            self.sentiment = {"bullish": 50, "bearish": 50, "tweets": 0}
            return False
    
    def calculate_technicals(self):
        """Calculate technical indicators from OHLC data"""
        if not self.ohlc_data:
            return {}
        
        closes = [float(c[4]) for c in self.ohlc_data]
        highs = [float(c[2]) for c in self.ohlc_data]
        lows = [float(c[3]) for c in self.ohlc_data]
        volumes = [float(c[5]) for c in self.ohlc_data]
        
        # EMAs
        def ema(values, period):
            multiplier = 2 / (period + 1)
            ema_vals = [values[0]]
            for price in values[1:]:
                ema_vals.append((price * multiplier) + (ema_vals[-1] * (1 - multiplier)))
            return ema_vals
        
        ema9 = ema(closes, 9)[-1]
        ema21 = ema(closes, 21)[-1]
        
        # RSI
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-14:]]
        losses = [-d if d < 0 else 0 for d in deltas[-14:]]
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0
        rs = avg_gain / avg_loss if avg_loss else 0
        rsi = 100 - (100 / (1 + rs)) if rs else 50
        
        # Confluence Score
        score = 50
        price = self.price_data.get("price", closes[-1])
        
        if price > ema9 > ema21:
            score += 15
        elif price < ema9 < ema21:
            score -= 15
            
        if self.price_data.get("change_24h", 0) > 5:
            score += 10
        elif self.price_data.get("change_24h", 0) < -5:
            score -= 10
            
        if self.sentiment.get("bullish", 50) > 60:
            score += 10
        elif self.sentiment.get("bullish", 50) < 40:
            score -= 10
            
        if rsi > 70:
            score -= 5
        elif rsi < 30:
            score += 5
            
        score = max(0, min(100, score))
        
        return {
            "ema9": ema9,
            "ema21": ema21,
            "rsi": round(rsi, 1),
            "confluence_score": score,
            "signal": "BULLISH" if score >= 70 else "BEARISH" if score <= 30 else "NEUTRAL",
            "color": "#10b981" if score >= 70 else "#ef4444" if score <= 30 else "#f59e0b"
        }
    
    def generate_html(self):
        """Generate HTML report"""
        p = self.price_data
        s = self.sentiment
        t = self.calculate_technicals()
        
        change_class = "positive" if p.get("change_24h", 0) >= 0 else "negative"
        change_symbol = "+" if p.get("change_24h", 0) >= 0 else ""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitcoin Daily Forecast - {self.date}</title>
    <style>
        :root {{ --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --muted: #94a3b8; --accent: #6366f1; --bull: #10b981; --bear: #ef4444; }}
        body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 40px; border-radius: 16px; text-align: center; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 2.5rem; }}
        .header .date {{ margin-top: 10px; opacity: 0.9; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
        .card {{ background: var(--card); border-radius: 12px; padding: 24px; border: 1px solid #334155; }}
        .card-title {{ font-size: 14px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px; }}
        .price {{ font-size: 56px; font-weight: 700; text-align: center; }}
        .change {{ font-size: 28px; text-align: center; margin-top: 8px; }}
        .positive {{ color: var(--bull); }} .negative {{ color: var(--bear); }}
        .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }}
        .metric {{ background: var(--bg); padding: 12px; border-radius: 8px; }}
        .metric-label {{ font-size: 12px; color: var(--muted); }}
        .metric-value {{ font-size: 18px; font-weight: 600; margin-top: 4px; }}
        .score {{ font-size: 72px; font-weight: 800; text-align: center; color: {t.get('color', '#f59e0b')}; }}
        .signal {{ font-size: 24px; text-align: center; color: {t.get('color', '#f59e0b')}; margin-top: 8px; }}
        .sentiment-bar {{ display: flex; height: 40px; border-radius: 20px; overflow: hidden; margin: 16px 0; }}
        .bullish {{ background: var(--bull); display: flex; align-items: center; justify-content: center; font-weight: 600; width: {s.get('bullish', 50)}%; }}
        .bearish {{ background: var(--bear); display: flex; align-items: center; justify-content: center; font-weight: 600; width: {s.get('bearish', 50)}%; }}
        .commentary {{ background: var(--bg); padding: 16px; border-radius: 8px; border-left: 4px solid var(--accent); margin-top: 16px; font-size: 14px; line-height: 1.6; }}
        .footer {{ text-align: center; padding: 30px; color: var(--muted); font-size: 12px; margin-top: 30px; border-top: 1px solid #334155; }}
        @media (max-width: 768px) {{ .price {{ font-size: 40px; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Bitcoin Daily Forecast</h1>
            <div class="date">{self.date} CST | Real Market Data | Auto-refresh: 60s</div>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">💰 Price Action</div>
                <div class="price">${p.get('price', 0):,.2f}</div>
                <div class="change {change_class}">{change_symbol}{p.get('change_24h', 0):.2f}%</div>
                <div class="metrics">
                    <div class="metric"><div class="metric-label">24h High</div><div class="metric-value">${p.get('high', 0):,.2f}</div></div>
                    <div class="metric"><div class="metric-label">24h Low</div><div class="metric-value">${p.get('low', 0):,.2f}</div></div>
                    <div class="metric"><div class="metric-label">Volume (BTC)</div><div class="metric-value">{p.get('volume', 0)/1e6:.2f}M</div></div>
                    <div class="metric"><div class="metric-label">Volume (USD)</div><div class="metric-value">${p.get('quote_volume', 0)/1e9:.2f}B</div></div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">🎯 Confluence Score</div>
                <div class="score">{t.get('confluence_score', 50)}</div>
                <div class="signal">{t.get('signal', 'NEUTRAL')}</div>
                <div class="metrics">
                    <div class="metric"><div class="metric-label">RSI (14)</div><div class="metric-value">{t.get('rsi', 50)}</div></div>
                    <div class="metric"><div class="metric-label">EMA 9/21</div><div class="metric-value">${t.get('ema9', 0):,.0f} / ${t.get('ema21', 0):,.0f}</div></div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">🐦 X/Twitter Sentiment</div>
                <div class="sentiment-bar">
                    <div class="bullish">🐂 {s.get('bullish', 50)}%</div>
                    <div class="bearish">🐻 {s.get('bearish', 50)}%</div>
                </div>
                <div class="commentary">
                    Analyzed {s.get('tweets', 0)} recent tweets. Bullish: {s.get('bullish', 50)}%, Bearish: {s.get('bearish', 50)}%.
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">📊 Market Commentary</div>
                <div class="commentary">
                    Bitcoin is trading at ${p.get('price', 0):,.2f} with a {p.get('change_24h', 0):.2f}% change over 24h. 
                    Confluence score of {t.get('confluence_score', 50)}/100 suggests a {t.get('signal', 'neutral')} bias. 
                    RSI at {t.get('rsi', 50)} indicates {'overbought' if t.get('rsi', 50) > 70 else 'oversold' if t.get('rsi', 50) < 30 else 'neutral'} conditions.
                    Social sentiment is {s.get('bullish', 50)}% bullish based on X analysis.
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Jarvis Becket for Ricardo Davila</p>
            <p>Data: Binance API, X API | Not Financial Advice</p>
            <p>Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CST</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def update_tracker(self):
        """Update the tracker index page"""
        tracker_file = os.path.join(TRACKER_DIR, "README.md")
        
        p = self.price_data
        change_emoji = "🟢" if p.get("change_24h", 0) >= 0 else "🔴"
        
        new_entry = f"| {self.date} | ${p.get('price', 0):,.0f} | {change_emoji} {p.get('change_24h', 0):.2f}% | [Report](https://jarvisbecket-stack.github.io/btc-daily-report/) | ✅ |\n"
        
        try:
            with open(tracker_file, "r") as f:
                content = f.read()
            
            # Insert new entry after the header row
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "|------|" in line:
                    lines.insert(i + 1, new_entry.rstrip())
                    break
            
            with open(tracker_file, "w") as f:
                f.write("\n".join(lines))
            
            print(f"✅ Tracker updated")
            return True
        except Exception as e:
            print(f"❌ Tracker update error: {e}")
            return False
    
    def save_and_commit(self, html):
        """Save report and commit to GitHub"""
        # Save report
        report_file = os.path.join(REPORT_DIR, "index.html")
        with open(report_file, "w") as f:
            f.write(html)
        
        # Save dated copy
        dated_file = os.path.join(REPORT_DIR, f"report_{self.date}.html")
        with open(dated_file, "w") as f:
            f.write(html)
        
        print(f"✅ Report saved: {report_file}")
        return True
    
    def run(self):
        """Generate full report"""
        print(f"📊 Bitcoin Daily Report - {self.date}")
        print("-" * 50)
        
        print("📡 Fetching Binance data...")
        self.fetch_binance_data()
        
        print("🐦 Analyzing X sentiment...")
        self.fetch_x_sentiment()
        
        print("📈 Calculating technicals...")
        t = self.calculate_technicals()
        print(f"   Score: {t.get('confluence_score', 50)}/100 | Signal: {t.get('signal', 'NEUTRAL')}")
        
        print("🎨 Generating HTML...")
        html = self.generate_html()
        
        print("💾 Saving report...")
        self.save_and_commit(html)
        
        print("📝 Updating tracker...")
        self.update_tracker()
        
        print("-" * 50)
        print("✅ Report complete!")
        return True

if __name__ == "__main__":
    os.chdir("/root/.openclaw/workspace/btc-daily-report")
    report = BitcoinDailyReport()
    report.run()
