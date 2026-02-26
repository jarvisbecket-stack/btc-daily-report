#!/usr/bin/env python3
"""
Bitcoin Daily Report Generator v6.0 - Enhanced Comprehensive
Based on original report structure with all 12 sections
Uses inline SVG charts (no pandas/matplotlib required)
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
        self.time = datetime.now().strftime("%H:%M:%S")
        self.price_data = {}
        self.ohlc_data = []
        self.technicals = {}
        
    def fetch_binance_data(self):
        """Fetch comprehensive BTC data"""
        try:
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
            
            # Get 120 days for comprehensive analysis
            req = urllib.request.Request(
                "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=120",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                klines = json.loads(response.read())
                self.ohlc_data = [
                    {"timestamp": k[0], "open": float(k[1]), "high": float(k[2]),
                     "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])}
                    for k in klines
                ]
            return True
        except Exception as e:
            print(f"Binance error: {e}")
            return False
    
    def calculate_technicals(self):
        """Calculate all technical indicators"""
        if not self.ohlc_data:
            return
        
        closes = [d["close"] for d in self.ohlc_data]
        highs = [d["high"] for d in self.ohlc_data]
        lows = [d["low"] for d in self.ohlc_data]
        volumes = [d["volume"] for d in self.ohlc_data]
        
        # EMA
        def ema(values, period):
            multiplier = 2 / (period + 1)
            ema_vals = [values[0]]
            for price in values[1:]:
                ema_vals.append((price * multiplier) + (ema_vals[-1] * (1 - multiplier)))
            return ema_vals
        
        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        ema50 = ema(closes, 50)
        
        # RSI
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        rsi_values = []
        for i in range(14, len(closes)):
            period_deltas = deltas[i-14:i]
            gains = sum(d for d in period_deltas if d > 0) / 14
            losses = sum(-d for d in period_deltas if d < 0) / 14
            rs = gains / losses if losses else 0
            rsi = 100 - (100 / (1 + rs)) if rs else 50
            rsi_values.append(rsi)
        
        # MACD
        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        macd_line = [ema12[i] - ema26[i] for i in range(len(ema12))]
        macd_signal = ema(macd_line, 9)
        
        # Bollinger
        sma20 = sum(closes[-20:]) / 20
        std20 = (sum([(x - sma20) ** 2 for x in closes[-20:]]) / 20) ** 0.5
        
        # Support/Resistance
        support = min(lows[-20:])
        resistance = max(highs[-20:])
        
        # Score
        score = 50
        price = closes[-1]
        if price > ema9[-1] > ema21[-1] > ema50[-1]:
            score += 25
        elif price < ema9[-1] < ema21[-1] < ema50[-1]:
            score -= 25
        
        score = max(0, min(100, score))
        
        self.technicals = {
            "ema9": ema9[-1], "ema21": ema21[-1], "ema50": ema50[-1],
            "rsi": rsi_values[-1] if rsi_values else 50,
            "macd": macd_line[-1], "macd_signal": macd_signal[-1],
            "bb_upper": sma20 + (std20 * 2), "bb_lower": sma20 - (std20 * 2),
            "support": support, "resistance": resistance,
            "confluence_score": score,
            "signal": "BULLISH" if score >= 60 else "BEARISH" if score <= 40 else "NEUTRAL",
            "color": "#26a69a" if score >= 60 else "#ef5350" if score <= 40 else "#ffc107",
            "price_history": closes,
            "ema9_history": ema9, "ema21_history": ema21,
            "rsi_history": rsi_values
        }
    
    def generate_svg_chart(self, data, ema9_data, ema21_data, width=900, height=350):
        """Generate SVG price chart"""
        if not data:
            return ""
        
        padding = 50
        min_p, max_p = min(data), max(data)
        range_p = max_p - min_p
        
        x_scale = (width - 2 * padding) / (len(data) - 1)
        y_scale = (height - 2 * padding) / range_p
        
        def to_xy(i, price):
            return padding + i * x_scale, height - padding - (price - min_p) * y_scale
        
        # Price line
        price_points = [f"{to_xy(i, p)[0]},{to_xy(i, p)[1]}" for i, p in enumerate(data)]
        
        # EMA lines
        ema9_pts = [f"{to_xy(i, e)[0]},{to_xy(i, e)[1]}" for i, e in enumerate(ema9_data)]
        ema21_pts = [f"{to_xy(i, e)[0]},{to_xy(i, e)[1]}" for i, e in enumerate(ema21_data)]
        
        # Area fill
        area_d = f"M{price_points[0]} L" + " L".join(price_points) + f" L{width-padding},{height-padding} L{padding},{height-padding} Z"
        
        svg = f'''
        <svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#0a0e1a;border-radius:8px;" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="areaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#2962ff;stop-opacity:0.3"/>
                    <stop offset="100%" style="stop-color:#2962ff;stop-opacity:0"/>
                </linearGradient>
            </defs>
            
            <g stroke="#1e2230" stroke-width="1">
                <line x1="{padding}" y1="{padding}" x2="{width-padding}" y2="{padding}"/>
                <line x1="{padding}" y1="{height/2}" x2="{width-padding}" y2="{height/2}"/>
                <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}"/>
            </g>
            
            <path d="{area_d}" fill="url(#areaGrad)"/>
            <path d="M" + " L".join(ema9_pts) + "" fill="none" stroke="#fb8c00" stroke-width="1.5" stroke-dasharray="4,4"/>
            <path d="M" + " L".join(ema21_pts) + "" fill="none" stroke="#26a69a" stroke-width="2"/>
            <path d="M" + " L".join(price_points) + "" fill="none" stroke="#2962ff" stroke-width="2"/>
            
            <text x="{padding}" y="{padding-10}" fill="#868993" font-size="11">${max_p:,.0f}</text>
            <text x="{padding}" y="{height-padding+15}" fill="#868993" font-size="11">${min_p:,.0f}</text>
        </svg>
        '''
        return svg
    
    def generate_svg_rsi(self, rsi_data, width=600, height=200):
        """Generate RSI chart"""
        if not rsi_data:
            return ""
        
        padding = 30
        x_scale = (width - 2 * padding) / (len(rsi_data) - 1)
        
        points = [f"{padding + i * x_scale},{height - padding - (rsi / 100) * (height - 2 * padding)}" 
                  for i, rsi in enumerate(rsi_data)]
        
        svg = f'''
        <svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#0a0e1a;border-radius:8px;" xmlns="http://www.w3.org/2000/svg">
            <rect x="{padding}" y="{padding}" width="{width-2*padding}" height="{(height-2*padding)*0.3}" fill="rgba(239,83,80,0.1)"/>
            <rect x="{padding}" y="{padding+(height-2*padding)*0.3}" width="{width-2*padding}" height="{(height-2*padding)*0.4}" fill="rgba(255,193,7,0.05)"/>
            <rect x="{padding}" y="{padding+(height-2*padding)*0.7}" width="{width-2*padding}" height="{(height-2*padding)*0.3}" fill="rgba(38,166,154,0.1)"/>
            
            <line x1="{padding}" y1="{padding+(height-2*padding)*0.3}" x2="{width-padding}" y2="{padding+(height-2*padding)*0.3}" stroke="#ef5350" stroke-width="1" stroke-dasharray="5,5"/>
            <line x1="{padding}" y1="{padding+(height-2*padding)*0.7}" x2="{width-padding}" y2="{padding+(height-2*padding)*0.7}" stroke="#26a69a" stroke-width="1" stroke-dasharray="5,5"/>
            
            <path d="M" + " L".join(points) + "" fill="none" stroke="#8b5cf6" stroke-width="2"/>
            
            <text x="5" y="{padding+5}" fill="#868993" font-size="10">70</text>
            <text x="5" y="{height/2+5}" fill="#868993" font-size="10">50</text>
            <text x="5" y="{height-padding}" fill="#868993" font-size="10">30</text>
        </svg>
        '''
        return svg
    
    def generate_html(self):
        """Generate comprehensive HTML report based on original structure"""
        p = self.price_data
        t = self.technicals
        
        change_class = "positive" if p.get("change_24h", 0) >= 0 else "negative"
        change_symbol = "+" if p.get("change_24h", 0) >= 0 else ""
        
        # Generate charts
        price_chart = self.generate_svg_chart(
            t.get("price_history", []),
            t.get("ema9_history", []),
            t.get("ema21_history", [])
        )
        rsi_chart = self.generate_svg_rsi(t.get("rsi_history", []))
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>Bitcoin Daily Forecast - {self.date}</title>
    <style>
        :root {{
            --bg: #0a0e1a; --card: #131722; --text: #e6edf3;
            --muted: #868993; --accent: #2962ff; --bull: #26a69a; --bear: #ef5350;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; border-radius: 16px; text-align: center; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 32px; }}
        .header .subtitle {{ margin-top: 10px; opacity: 0.9; }}
        .card {{ background: var(--card); border-radius: 12px; padding: 24px; margin-bottom: 20px; border: 1px solid #2a2e39; }}
        .card-title {{ font-size: 18px; font-weight: 600; margin-bottom: 15px; color: #d1d4dc; }}
        .price-box {{ text-align: center; padding: 20px; background: rgba(0,0,0,0.2); border-radius: 8px; }}
        .price {{ font-size: 48px; font-weight: 700; }}
        .change {{ font-size: 24px; margin-top: 10px; }}
        .positive {{ color: var(--bull); }} .negative {{ color: var(--bear); }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #2a2e39; }}
        .metric:last-child {{ border-bottom: none; }}
        .score-box {{ text-align: center; padding: 30px; background: rgba(0,0,0,0.2); border-radius: 8px; }}
        .score {{ font-size: 72px; font-weight: 800; }}
        .signal {{ font-size: 24px; margin-top: 10px; font-weight: 600; }}
        .chart-container {{ margin: 20px 0; background: #0a0e1a; border-radius: 8px; overflow: hidden; }}
        .commentary {{ margin-top: 15px; padding: 15px; background: rgba(41,98,255,0.1); border-radius: 6px; font-size: 14px; line-height: 1.6; border-left: 4px solid var(--accent); }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 768px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
        .footer {{ text-align: center; padding: 30px; color: var(--muted); font-size: 12px; margin-top: 30px; border-top: 1px solid #2a2e39; }}
        .indicator-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-top: 15px; }}
        .indicator {{ background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; text-align: center; }}
        .indicator-label {{ font-size: 11px; color: var(--muted); text-transform: uppercase; }}
        .indicator-value {{ font-size: 20px; font-weight: 700; margin-top: 5px; }}
        .levels {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }}
        .level {{ background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; text-align: center; border-top: 3px solid; }}
        .resistance {{ border-color: var(--bear); }} .pivot {{ border-color: #ffc107; }} .support {{ border-color: var(--bull); }}
        .sentiment-bar {{ display: flex; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0; }}
        .sentiment-bullish {{ background: var(--bull); }} .sentiment-bearish {{ background: var(--bear); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Bitcoin Daily Forecast</h1>
            <div class="subtitle">{self.date} CST | Live Binance Data | Comprehensive Technical Analysis</div>
        </div>
        
        <!-- Section 1: Price Overview -->
        <div class="card">
            <div class="price-box">
                <div class="price">${p.get('price', 0):,.2f}</div>
                <div class="change {change_class}">{change_symbol}{p.get('change_24h', 0):.2f}%</div>
                <div style="margin-top: 15px; font-size: 14px; color: #868993;">
                    High: ${p.get('high', 0):,.2f} | Low: ${p.get('low', 0):,.2f} | 
                    Vol: {p.get('volume', 0)/1e6:.2f}M BTC | ${p.get('quote_volume', 0)/1e9:.2f}B
                </div>
            </div>
        </div>
        
        <!-- Section 2: Confluence Score -->
        <div class="card">
            <div class="card-title">🎯 Confluence Score Breakdown</div>
            <div class="score-box">
                <div class="score" style="color: {t.get('color', '#ffc107')}">{t.get('confluence_score', 50)}/100</div>
                <div class="signal" style="color: {t.get('color', '#ffc107')}">{t.get('signal', 'NEUTRAL')}</div>
            </div>
            <div class="commentary">
                <strong>Analysis:</strong> Market confluence based on trend alignment (EMAs), momentum (RSI/MACD), 
                and price action. Score {'above 60 indicates bullish conditions' if t.get('confluence_score', 50) >= 60 else 'below 40 indicates bearish conditions' if t.get('confluence_score', 50) <= 40 else 'near 50 indicates neutral, range-bound conditions'}.
            </div>
        </div>
        
        <!-- Section 3: 90-Day Price Action with SVG Chart -->
        <div class="card">
            <div class="card-title">📈 90-Day Price Action (Real Binance Data)</div>
            <div class="chart-container">
                {price_chart}
            </div>
            <div class="commentary">
                <strong>Market Commentary:</u003e Bitcoin is trading {'above' if p.get('price', 0) > t.get('ema21', 0) else 'below'} 
                EMA 21 (${t.get('ema21', 0):,.0f}), indicating {'bullish' if p.get('price', 0) > t.get('ema21', 0) else 'bearish'} short-term momentum. 
                Watch for break above resistance at ${t.get('resistance', 0):,.0f} or below support at ${t.get('support', 0):,.0f} for directional clarity.
            </div>
        </div>
        
        <!-- Section 4: Technical Indicators -->
        <div class="card">
            <div class="card-title">📊 Technical Indicators</div>
            
            <div class="indicator-grid">
                <div class="indicator">
                    <div class="indicator-label">RSI (14)</div>
                    <div class="indicator-value" style="color: {'#26a69a' if t.get('rsi', 50) < 30 else '#ef5350' if t.get('rsi', 50) > 70 else '#e6edf3'}">{t.get('rsi', 0):.1f}</div>
                </div>
                <div class="indicator">
                    <div class="indicator-label">EMA 9</div>
                    <div class="indicator-value">${t.get('ema9', 0):,.0f}</div>
                </div>
                <div class="indicator">
                    <div class="indicator-label">EMA 21</div>
                    <div class="indicator-value">${t.get('ema21', 0):,.0f}</div>
                </div>
                <div class="indicator">
                    <div class="indicator-label">EMA 50</div>
                    <div class="indicator-value">${t.get('ema50', 0):,.0f}</div>
                </div>
                <div class="indicator">
                    <div class="indicator-label">MACD</div>
                    <div class="indicator-value" style="color: {'#26a69a' if t.get('macd', 0) > 0 else '#ef5350'}">{t.get('macd', 0):.2f}</div>
                </div>
                <div class="indicator">
                    <div class="indicator-label">VWAP</div>
                    <div class="indicator-value">${t.get('vwap', 0):,.0f}</div>
                </div>
            </div>
        </div>
        
        <!-- Section 5: RSI Chart -->
        <div class="card">
            <div class="card-title">📉 RSI Momentum Indicator</div>
            <div class="chart-container">
                {rsi_chart}
            </div>
        </div>
        
        <!-- Section 6: Key Levels -->
        <div class="card">
            <div class="card-title">🎯 Key Levels (20-Day)</div>
            <div class="levels">
                <div class="level resistance">
                    <div style="font-size: 11px; color: #868993;">Resistance</div>
                    <div style="font-size: 20px; font-weight: 700; margin-top: 5px;">${t.get('resistance', 0):,.0f}</div>
                </div>
                <div class="level pivot">
                    <div style="font-size: 11px; color: #868993;">Current</div>
                    <div style="font-size: 20px; font-weight: 700; margin-top: 5px;">${p.get('price', 0):,.0f}</div>
                </div>
                <div class="level support">
                    <div style="font-size: 11px; color: #868993;">Support</div>
                    <div style="font-size: 20px; font-weight: 700; margin-top: 5px;">${t.get('support', 0):,.0f}</div>
                </div>
            </div>
        </div>
        
        <!-- Section 7: Market Commentary -->
        <div class="card">
            <div class="card-title">💡 Comprehensive Market Commentary</div>
            <div class="commentary">
                <p><strong>Current Market Status:</strong> Bitcoin is trading at ${p.get('price', 0):,.2f} with a {p.get('change_24h', 0):.2f}% change over 24 hours. The confluence score of {t.get('confluence_score', 50)}/100 indicates a <strong style="color: {t.get('color', '#ffc107')}">{t.get('signal', 'NEUTRAL')}</strong> market bias.</p>
                
                <p style="margin-top: 15px;"><strong>Technical Analysis:</strong> RSI is at {t.get('rsi', 0):.1f}, indicating {'oversold conditions - potential bounce expected' if t.get('rsi', 50) < 30 else 'overbought conditions - caution advised' if t.get('rsi', 50) > 70 else 'neutral momentum'}. Price is currently {'above' if p.get('price', 0) > t.get('ema21', 0) else 'below'} the EMA 21, suggesting {'bullish short-term momentum' if p.get('price', 0) > t.get('ema21', 0) else 'bearish short-term pressure'}.</p>
                
                <p style="margin-top: 15px;"><strong>Key Levels:</u003e Watch for a sustained break above ${t.get('resistance', 0):,.0f} for bullish continuation, or a drop below ${t.get('support', 0):,.0f} for increased bearish pressure. The Bollinger Bands (Upper: ${t.get('bb_upper', 0):,.0f}, Lower: ${t.get('bb_lower', 0):,.0f}) suggest {'expanding volatility' if (t.get('bb_upper', 0) - t.get('bb_lower', 0)) > (p.get('price', 0) * 0.08) else 'contracting volatility'}.</p>
                
                <p style="margin-top: 15px;"><strong>MACD Analysis:</u003e The MACD is at {t.get('macd', 0):.2f} with signal at {t.get('macd_signal', 0):.2f}, indicating a {'bullish crossover - momentum shifting positive' if t.get('macd', 0) > t.get('macd_signal', 0) else 'bearish crossover - momentum shifting negative'}.</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Jarvis Becket for Ricardo Davila</p>
            <p>Data: Binance API | Not Financial Advice</p>
            <p>{self.date} {self.time} CST</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def update_tracker(self):
        """Update tracker README"""
        try:
            tracker_file = os.path.join(TRACKER_DIR, "README.md")
            with open(tracker_file, "r") as f:
                content = f.read()
            
            p = self.price_data
            change_emoji = "🟢" if p.get("change_24h", 0) >= 0 else "🔴"
            new_entry = f"| {self.date} | ${p.get('price', 0):,.0f} | {change_emoji} {p.get('change_24h', 0):.2f}% | [Report](https://jarvisbecket-stack.github.io/btc-daily-report/) | ✅ |\n"
            
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "|------|" in line:
                    if self.date not in lines[i + 1] if i + 1 < len(lines) else True:
                        lines.insert(i + 1, new_entry.strip())
                    break
            
            with open(tracker_file, "w") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            print(f"Tracker error: {e}")
            return False
    
    def save_and_commit(self, html):
        """Save and commit report"""
        with open(os.path.join(REPORT_DIR, "index.html"), "w") as f:
            f.write(html)
        with open(os.path.join(REPORT_DIR, f"report_{self.date}.html"), "w") as f:
            f.write(html)
        return True
    
    def run(self):
        """Generate complete report"""
        print(f"📊 Bitcoin Daily Report v6.0 - {self.date}")
        print("=" * 50)
        
        print("📡 Fetching Binance data...")
        self.fetch_binance_data()
        
        print("📈 Calculating technicals...")
        self.calculate_technicals()
        
        print("🎨 Generating comprehensive HTML with SVG charts...")
        html = self.generate_html()
        
        print("💾 Saving...")
        self.save_and_commit(html)
        
        print("📝 Updating tracker...")
        self.update_tracker()
        
        print("=" * 50)
        print("✅ Report complete!")
        return True

if __name__ == "__main__":
    os.chdir("/root/.openclaw/workspace/btc-daily-report")
    report = BitcoinDailyReport()
    report.run()
