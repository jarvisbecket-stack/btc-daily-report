#!/usr/bin/env python3
"""
Bitcoin Daily Report Generator v5.0 - Enhanced
Comprehensive report with SVG charts, TTC analysis, technical indicators
No external dependencies - pure Python
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
        self.sentiment = {}
        self.technicals = {}
        
    def fetch_binance_data(self):
        """Fetch BTC data from Binance"""
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
            
            # Get 90 days of OHLC data
            req = urllib.request.Request(
                "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=90",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                klines = json.loads(response.read())
                self.ohlc_data = [
                    {
                        "timestamp": k[0],
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5])
                    }
                    for k in klines
                ]
            return True
        except Exception as e:
            print(f"Binance error: {e}")
            return False
    
    def calculate_technicals(self):
        """Calculate technical indicators"""
        if not self.ohlc_data:
            return
        
        closes = [d["close"] for d in self.ohlc_data]
        highs = [d["high"] for d in self.ohlc_data]
        lows = [d["low"] for d in self.ohlc_data]
        volumes = [d["volume"] for d in self.ohlc_data]
        
        # EMA calculations
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
        gains = [d if d > 0 else 0 for d in deltas[-14:]]
        losses = [-d if d < 0 else 0 for d in deltas[-14:]]
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0
        rs = avg_gain / avg_loss if avg_loss else 0
        rsi = 100 - (100 / (1 + rs)) if rs else 50
        
        # MACD
        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        macd_line = [ema12[i] - ema26[i] for i in range(len(ema12))]
        macd_signal = ema(macd_line, 9)
        macd_hist = [macd_line[i] - macd_signal[i] for i in range(len(macd_line))]
        
        # Bollinger Bands
        sma20 = sum(closes[-20:]) / 20
        std20 = (sum([(x - sma20) ** 2 for x in closes[-20:]]) / 20) ** 0.5
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)
        
        # VWAP
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
        vwap = sum([tp * v for tp, v in zip(typical_prices, volumes)]) / sum(volumes)
        
        # Support/Resistance (simple)
        support = min(lows[-20:])
        resistance = max(highs[-20:])
        
        # Confluence Score
        score = 50
        price = closes[-1]
        
        if price > ema9[-1] > ema21[-1] > ema50[-1]:
            score += 20
        elif price < ema9[-1] < ema21[-1] < ema50[-1]:
            score -= 20
        
        if self.price_data.get("change_24h", 0) > 5:
            score += 10
        elif self.price_data.get("change_24h", 0) < -5:
            score -= 10
        
        if rsi > 70:
            score -= 5
        elif rsi < 30:
            score += 5
        
        score = max(0, min(100, score))
        
        self.technicals = {
            "ema9": ema9[-1],
            "ema21": ema21[-1],
            "ema50": ema50[-1],
            "rsi": round(rsi, 2),
            "macd": round(macd_line[-1], 2),
            "macd_signal": round(macd_signal[-1], 2),
            "macd_hist": round(macd_hist[-1], 2),
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "bb_middle": sma20,
            "vwap": vwap,
            "support": support,
            "resistance": resistance,
            "confluence_score": score,
            "signal": "BULLISH" if score >= 70 else "BEARISH" if score <= 30 else "NEUTRAL",
            "color": "#10b981" if score >= 70 else "#ef4444" if score <= 30 else "#f59e0b"
        }
    
    def generate_svg_chart_90day(self):
        """Generate 90-day price chart as SVG"""
        if not self.ohlc_data:
            return ""
        
        width = 800
        height = 300
        padding = 40
        
        prices = [d["close"] for d in self.ohlc_data]
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        
        # Scale functions
        x_scale = (width - 2 * padding) / (len(prices) - 1)
        y_scale = (height - 2 * padding) / price_range
        
        # Generate line path
        points = []
        for i, price in enumerate(prices):
            x = padding + i * x_scale
            y = height - padding - (price - min_price) * y_scale
            points.append(f"{x},{y}")
        
        path_d = "M" + " L".join(points)
        
        # EMA lines
        ema9_points = []
        ema21_points = []
        
        closes = prices
        def ema_calc(values, period):
            multiplier = 2 / (period + 1)
            ema_vals = [values[0]]
            for price in values[1:]:
                ema_vals.append((price * multiplier) + (ema_vals[-1] * (1 - multiplier)))
            return ema_vals
        
        ema9_vals = ema_calc(closes, 9)
        ema21_vals = ema_calc(closes, 21)
        
        for i, (e9, e21) in enumerate(zip(ema9_vals, ema21_vals)):
            x = padding + i * x_scale
            y9 = height - padding - (e9 - min_price) * y_scale
            y21 = height - padding - (e21 - min_price) * y_scale
            ema9_points.append(f"{x},{y9}")
            ema21_points.append(f"{x},{y21}")
        
        ema9_path = "M" + " L".join(ema9_points)
        ema21_path = "M" + " L".join(ema21_points)
        
        svg = f'''
        <svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="priceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#6366f1;stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:#6366f1;stop-opacity:0" />
                </linearGradient>
            </defs>
            
            <!-- Grid lines -->
            <g stroke="#2a2a3a" stroke-width="1">
                <line x1="{padding}" y1="{padding}" x2="{width-padding}" y2="{padding}" />
                <line x1="{padding}" y1="{height/2}" x2="{width-padding}" y2="{height/2}" />
                <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" />
            </g>
            
            <!-- Price area fill -->
            <path d="{path_d} L{width-padding},{height-padding} L{padding},{height-padding} Z" fill="url(#priceGradient)" />
            
            <!-- Price line -->
            <path d="{path_d}" fill="none" stroke="#6366f1" stroke-width="2" />
            
            <!-- EMA 9 -->
            <path d="{ema9_path}" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="5,5" />
            
            <!-- EMA 21 -->
            <path d="{ema21_path}" fill="none" stroke="#10b981" stroke-width="1.5" />
            
            <!-- Labels -->
            <text x="{padding}" y="{padding-10}" fill="#94a3b8" font-size="12">${max_price:,.0f}</text>
            <text x="{padding}" y="{height-padding+15}" fill="#94a3b8" font-size="12">${min_price:,.0f}</text>
            
            <!-- Legend -->
            <g transform="translate({width-200}, 20)">
                <line x1="0" y1="0" x2="20" y2="0" stroke="#6366f1" stroke-width="2" />
                <text x="25" y="5" fill="#e2e8f0" font-size="12">Price</text>
                <line x1="0" y1="20" x2="20" y2="20" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="5,5" />
                <text x="25" y="25" fill="#e2e8f0" font-size="12">EMA 9</text>
                <line x1="0" y1="40" x2="20" y2="40" stroke="#10b981" stroke-width="1.5" />
                <text x="25" y="45" fill="#e2e8f0" font-size="12">EMA 21</text>
            </g>
        </svg>
        '''
        return svg
    
    def generate_svg_rsi(self):
        """Generate RSI chart"""
        if not self.ohlc_data:
            return ""
        
        closes = [d["close"] for d in self.ohlc_data]
        
        # Calculate RSI values
        rsi_values = []
        for i in range(14, len(closes)):
            deltas = [closes[j] - closes[j-1] for j in range(i-13, i+1)]
            gains = [d for d in deltas if d > 0]
            losses = [-d for d in deltas if d < 0]
            avg_gain = sum(gains) / 14 if gains else 0
            avg_loss = sum(losses) / 14 if losses else 0
            rs = avg_gain / avg_loss if avg_loss else 0
            rsi = 100 - (100 / (1 + rs)) if rs else 50
            rsi_values.append(rsi)
        
        width = 600
        height = 200
        padding = 30
        
        x_scale = (width - 2 * padding) / (len(rsi_values) - 1)
        
        points = []
        for i, rsi in enumerate(rsi_values):
            x = padding + i * x_scale
            y = height - padding - (rsi / 100) * (height - 2 * padding)
            points.append(f"{x},{y}")
        
        path_d = "M" + " L".join(points)
        
        svg = f'''
        <svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;" xmlns="http://www.w3.org/2000/svg">
            <!-- Background zones -->
            <rect x="{padding}" y="{padding}" width="{width-2*padding}" height="{(height-2*padding)*0.3}" fill="rgba(16,185,129,0.1)" />
            <rect x="{padding}" y="{padding+(height-2*padding)*0.3}" width="{width-2*padding}" height="{(height-2*padding)*0.4}" fill="rgba(245,158,11,0.05)" />
            <rect x="{padding}" y="{padding+(height-2*padding)*0.7}" width="{width-2*padding}" height="{(height-2*padding)*0.3}" fill="rgba(239,68,68,0.1)" />
            
            <!-- Overbought/oversold lines -->
            <line x1="{padding}" y1="{padding+(height-2*padding)*0.3}" x2="{width-padding}" y2="{padding+(height-2*padding)*0.3}" stroke="#ef4444" stroke-width="1" stroke-dasharray="5,5" />
            <line x1="{padding}" y1="{padding+(height-2*padding)*0.7}" x2="{width-padding}" y2="{padding+(height-2*padding)*0.7}" stroke="#10b981" stroke-width="1" stroke-dasharray="5,5" />
            
            <!-- RSI line -->
            <path d="{path_d}" fill="none" stroke="#8b5cf6" stroke-width="2" />
            
            <!-- Labels -->
            <text x="5" y="{padding+5}" fill="#94a3b8" font-size="10">70</text>
            <text x="5" y="{height/2+5}" fill="#94a3b8" font-size="10">50</text>
            <text x="5" y="{height-padding}" fill="#94a3b8" font-size="10">30</text>
            
            <!-- Current value -->
            <text x="{width/2}" y="20" fill="#8b5cf6" font-size="14" font-weight="bold" text-anchor="middle">RSI: {rsi_values[-1]:.1f}</text>
        </svg>
        '''
        return svg
    
    def generate_html(self):
        """Generate comprehensive HTML report"""
        p = self.price_data
        t = self.technicals
        
        change_class = "positive" if p.get("change_24h", 0) >= 0 else "negative"
        change_symbol = "+" if p.get("change_24h", 0) >= 0 else ""
        
        chart_90d = self.generate_svg_chart_90day()
        chart_rsi = self.generate_svg_rsi()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Bitcoin Daily Forecast - {self.date}</title>
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a25;
            --bg-hover: #252535;
            --text-primary: #e8e8f0;
            --text-secondary: #94a3b8;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-success: #10b981;
            --accent-warning: #f59e0b;
            --accent-danger: #ef4444;
            --border-color: #2a2a3a;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}
        header {{
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 2rem 1rem;
            text-align: center;
        }}
        .logo {{ font-size: 3rem; margin-bottom: 0.5rem; }}
        h1 {{
            font-size: 2rem;
            background: linear-gradient(135deg, var(--text-primary), var(--accent-primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: var(--text-secondary); margin-top: 0.5rem; }}
        .report-date {{
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border-radius: 20px;
            color: var(--accent-primary);
        }}
        nav {{
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            padding: 0.75rem;
            position: sticky;
            top: 0;
            z-index: 100;
            overflow-x: auto;
        }}
        .nav-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            gap: 0.5rem;
            justify-content: center;
        }}
        .nav-link {{
            color: var(--text-secondary);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            white-space: nowrap;
            transition: all 0.2s;
        }}
        .nav-link:hover {{ background: var(--bg-hover); color: var(--text-primary); }}
        main {{ max-width: 1200px; margin: 0 auto; padding: 2rem 1rem; }}
        section {{ margin-bottom: 3rem; }}
        .section-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--border-color);
        }}
        .section-icon {{ font-size: 1.5rem; }}
        h2 {{ font-size: 1.5rem; font-weight: 600; }}
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }}
        @media (max-width: 768px) {{ .card-grid {{ grid-template-columns: 1fr; }} }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.2s;
        }}
        .card:hover {{ border-color: var(--accent-primary); transform: translateY(-2px); }}
        .card-title {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 1rem;
        }}
        .price {{ font-size: 3rem; font-weight: 700; text-align: center; }}
        .change {{ font-size: 1.5rem; text-align: center; margin-top: 0.5rem; }}
        .positive {{ color: var(--accent-success); }}
        .negative {{ color: var(--accent-danger); }}
        .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }}
        .metric {{ background: var(--bg-secondary); padding: 1rem; border-radius: 8px; }}
        .metric-label {{ font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }}
        .metric-value {{ font-size: 1.25rem; font-weight: 600; margin-top: 0.25rem; }}
        .score-box {{ text-align: center; padding: 2rem; }}
        .score-value {{ font-size: 5rem; font-weight: 800; }}
        .score-label {{ font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem; text-transform: uppercase; }}
        .chart-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .chart-title {{
            font-weight: 600;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .indicator-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 1rem;
        }}
        .indicator {{
            background: var(--bg-secondary);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }}
        .indicator-label {{ font-size: 0.75rem; color: var(--text-secondary); }}
        .indicator-value {{ font-size: 1.5rem; font-weight: 700; margin-top: 0.25rem; }}
        .commentary {{
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid var(--accent-primary);
            font-size: 1rem;
            line-height: 1.8;
        }}
        .levels-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }}
        .level {{
            background: var(--bg-secondary);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }}
        .level-label {{ font-size: 0.75rem; color: var(--text-secondary); }}
        .level-value {{ font-size: 1.25rem; font-weight: 600; margin-top: 0.25rem; }}
        .resistance {{ border-top: 3px solid var(--accent-danger); }}
        .pivot {{ border-top: 3px solid var(--accent-warning); }}
        .support {{ border-top: 3px solid var(--accent-success); }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border-color);
            margin-top: 2rem;
        }}
    </style>
</head>
<body>
    <header>
        <div class="logo">📊</div>
        <h1>Bitcoin Daily Forecast</h1>
        <p class="subtitle">Comprehensive Technical Analysis with Real Market Data</p>
        <div class="report-date">📅 {self.date} | {self.time} CST</div>
    </header>
    
    <nav>
        <div class="nav-content">
            <a href="#overview" class="nav-link">Overview</a>
            <a href="#price-action" class="nav-link">Price Action</a>
            <a href="#indicators" class="nav-link">Indicators</a>
            <a href="#levels" class="nav-link">Levels</a>
            <a href="#commentary" class="nav-link">Commentary</a>
        </div>
    </nav>
    
    <main>
        <!-- Overview Section -->
        <section id="overview">
            <div class="section-header">
                <span class="section-icon">📈</span>
                <h2>Market Overview</h2>
            </div>
            
            <div class="card-grid">
                <div class="card">
                    <div class="card-title">Current Price</div>
                    <div class="price">${p.get('price', 0):,.2f}</div>
                    <div class="change {change_class}">{change_symbol}{p.get('change_24h', 0):.2f}%</div>
                </div>
                
                <div class="card">
                    <div class="card-title">Confluence Score</div>
                    <div class="score-box">
                        <div class="score-value" style="color: {t.get('color', '#f59e0b')}">{t.get('confluence_score', 50)}</div>
                        <div class="score-label" style="color: {t.get('color', '#f59e0b')}">{t.get('signal', 'NEUTRAL')}</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">24h Range</div>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-label">High</div>
                            <div class="metric-value">${p.get('high', 0):,.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Low</div>
                            <div class="metric-value">${p.get('low', 0):,.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Volume BTC</div>
                            <div class="metric-value">{p.get('volume', 0)/1e6:.2f}M</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Volume USD</div>
                            <div class="metric-value">${p.get('quote_volume', 0)/1e9:.2f}B</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Price Action Section -->
        <section id="price-action">
            <div class="section-header">
                <span class="section-icon">📉</span>
                <h2>Price Action (90-Day)</h2>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📊 Price Chart with EMA 9/21</div>
                {chart_90d}
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📈 RSI (14)</div>
                {chart_rsi}
            </div>
        </section>
        
        <!-- Technical Indicators Section -->
        <section id="indicators">
            <div class="section-header">
                <span class="section-icon">🎯</span>
                <h2>Technical Indicators</h2>
            </div>
            
            <div class="indicator-grid">
                <div class="indicator">
                    <div class="indicator-label">RSI (14)</div>
                    <div class="indicator-value" style="color: {'#10b981' if t.get('rsi', 50) < 30 else '#ef4444' if t.get('rsi', 50) > 70 else '#e8e8f0'}">{t.get('rsi', 0):.1f}</div>
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
                    <div class="indicator-value" style="color: {'#10b981' if t.get('macd', 0) > 0 else '#ef4444'}">{t.get('macd', 0):.2f}</div>
                </div>
                <div class="indicator">
                    <div class="indicator-label">VWAP</div>
                    <div class="indicator-value">${t.get('vwap', 0):,.0f}</div>
                </div>
            </div>
            
            <div class="chart-container" style="margin-top: 1.5rem;">
                <div class="chart-title">📊 Bollinger Bands</div>
                <div class="indicator-grid">
                    <div class="indicator">
                        <div class="indicator-label">Upper Band</div>
                        <div class="indicator-value">${t.get('bb_upper', 0):,.0f}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Middle (SMA 20)</div>
                        <div class="indicator-value">${t.get('bb_middle', 0):,.0f}</div>
                    </div>
                    <div class="indicator">
                        <div class="indicator-label">Lower Band</div>
                        <div class="indicator-value">${t.get('bb_lower', 0):,.0f}</div>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Key Levels Section -->
        <section id="levels">
            <div class="section-header">
                <span class="section-icon">🎯</span>
                <h2>Key Levels (20-Day)</h2>
            </div>
            
            <div class="levels-grid">
                <div class="level resistance">
                    <div class="level-label">Resistance</div>
                    <div class="level-value">${t.get('resistance', 0):,.0f}</div>
                </div>
                <div class="level pivot">
                    <div class="level-label">Current</div>
                    <div class="level-value">${p.get('price', 0):,.0f}</div>
                </div>
                <div class="level support">
                    <div class="level-label">Support</div>
                    <div class="level-value">${t.get('support', 0):,.0f}</div>
                </div>
            </div>
        </section>
        
        <!-- Commentary Section -->
        <section id="commentary">
            <div class="section-header">
                <span class="section-icon">💡</span>
                <h2>Market Commentary</h2>
            </div>
            
            <div class="commentary">
                <p><strong>Current Market Status:</strong> Bitcoin is trading at ${p.get('price', 0):,.2f} with a {p.get('change_24h', 0):.2f}% change over 24 hours. The confluence score of {t.get('confluence_score', 50)}/100 indicates a <strong>{t.get('signal', 'NEUTRAL')}</strong> market bias.</p>
                
                <p style="margin-top: 1rem;"><strong>Technical Analysis:</strong> RSI is at {t.get('rsi', 0):.1f}, indicating {'oversold' if t.get('rsi', 50) < 30 else 'overbought' if t.get('rsi', 50) > 70 else 'neutral'} conditions. Price is {'above' if p.get('price', 0) > t.get('ema21', 0) else 'below'} the EMA 21 (${t.get('ema21', 0):,.0f}), suggesting {'bullish' if p.get('price', 0) > t.get('ema21', 0) else 'bearish'} short-term momentum.</p>
                
                <p style="margin-top: 1rem;"><strong>Key Levels:</strong> Watch for a break above resistance at ${t.get('resistance', 0):,.0f} for bullish continuation, or a drop below support at ${t.get('support', 0):,.0f} for bearish pressure. The Bollinger Bands show {'expanding' if (t.get('bb_upper', 0) - t.get('bb_lower', 0)) > (p.get('price', 0) * 0.1) else 'contracting'} volatility.</p>
                
                <p style="margin-top: 1rem;"><strong>MACD Analysis:</strong> The MACD is at {t.get('macd', 0):.2f} with signal at {t.get('macd_signal', 0):.2f}, indicating a {'bullish' if t.get('macd', 0) > t.get('macd_signal', 0) else 'bearish'} crossover signal.</p>
            </div>
        </section>
    </main>
    
    <footer>
        <p>Generated by Jarvis Becket for Ricardo Davila</p>
        <p style="margin-top: 0.5rem;">Data: Binance API | Not Financial Advice</p>
        <p style="margin-top: 0.5rem;">{self.date} {self.time} CST</p>
    </footer>
</body>
</html>"""
        return html
    
    def update_tracker(self):
        """Update tracker"""
        try:
            tracker_file = os.path.join(TRACKER_DIR, "README.md")
            with open(tracker_file, "r") as f:
                content = f.read()
            
            p = self.price_data
            change_emoji = "🟢" if p.get("change_24h", 0) >= 0 else "🔴"
            new_entry = f"| {self.date} | ${p.get('price', 0):,.0f} | {change_emoji} {p.get('change_24h', 0):.2f}% | [Report](https://jarvisbecket-stack.github.io/btc-daily-report/) | ✅ |\n"
            
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "|------|" in line and i + 1 < len(lines):
                    if self.date not in lines[i + 1]:
                        lines.insert(i + 1, new_entry.strip())
                    break
            
            with open(tracker_file, "w") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            print(f"Tracker error: {e}")
            return False
    
    def save_and_commit(self, html):
        """Save report"""
        with open(os.path.join(REPORT_DIR, "index.html"), "w") as f:
            f.write(html)
        
        with open(os.path.join(REPORT_DIR, f"report_{self.date}.html"), "w") as f:
            f.write(html)
        
        return True
    
    def run(self):
        """Generate full report"""
        print(f"📊 Bitcoin Daily Report v5.0 - {self.date}")
        print("-" * 50)
        
        print("📡 Fetching Binance data...")
        self.fetch_binance_data()
        
        print("📈 Calculating technicals...")
        self.calculate_technicals()
        
        print("🎨 Generating HTML with charts...")
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
