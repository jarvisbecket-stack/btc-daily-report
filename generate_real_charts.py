#!/usr/bin/env python3
"""
Generate TradingView-quality candlestick charts using REAL Binance OHLC data
"""

import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json

# Parse the Binance kline data
# Format: [timestamp, open, high, low, close, volume, close_time, quote_volume, trades, ...]

binance_data = [
    [1761523200000, "114559.41000000", "116400.00000000", "113830.01000000", "114107.65000000", "21450.23241000"],
    [1761609600000, "114107.65000000", "116086.00000000", "112211.00000000", "112898.45000000", "15523.42257000"],
    [1761696000000, "112898.44000000", "113643.73000000", "109200.00000000", "110021.29000000", "21079.71376000"],
    [1761782400000, "110021.30000000", "111592.00000000", "106304.34000000", "108322.88000000", "25988.82838000"],
    [1761868800000, "108322.87000000", "111190.00000000", "108275.28000000", "109608.01000000", "21518.20439000"],
    # ... (truncated for brevity, using full data in actual script)
]

# Full data parsing from the API response
data_rows = []
with open('/tmp/binance_ohlc.json', 'r') as f:
    raw_data = json.load(f)

for row in raw_data:
    timestamp = row[0]
    open_price = float(row[1])
    high_price = float(row[2])
    low_price = float(row[3])
    close_price = float(row[4])
    volume = float(row[5])
    
    date = datetime.fromtimestamp(timestamp / 1000)
    
    data_rows.append({
        'Date': date,
        'Open': open_price,
        'High': high_price,
        'Low': low_price,
        'Close': close_price,
        'Volume': volume
    })

df = pd.DataFrame(data_rows)
df.set_index('Date', inplace=True)

print(f"Loaded {len(df)} days of real Binance OHLC data")
print(f"Date range: {df.index[0]} to {df.index[-1]}")
print(f"Price range: ${df['Low'].min():,.0f} - ${df['High'].max():,.0f}")

# Calculate indicators
df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

# Bollinger Bands
df['BB_Middle'] = df['Close'].rolling(window=20).mean()
df['BB_Std'] = df['Close'].rolling(window=20).std()
df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)

# VWAP
df['TPV'] = (df['Close'] + df['High'] + df['Low']) / 3 * df['Volume']
df['VWAP'] = df['TPV'].cumsum() / df['Volume'].cumsum()

# RSI
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['RSI'] = calculate_rsi(df['Close'])

# MACD
exp1 = df['Close'].ewm(span=12, adjust=False).mean()
exp2 = df['Close'].ewm(span=26, adjust=False).mean()
df['MACD'] = exp1 - exp2
df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# Style setup
mc = mpf.make_marketcolors(
    up='#10b981',
    down='#ef4444',
    edge='inherit',
    wick='inherit',
    volume='in'
)

s = mpf.make_mpf_style(
    marketcolors=mc,
    figcolor='white',
    facecolor='white',
    edgecolor='#e2e8f0',
    gridcolor='#f1f5f9',
    gridstyle='-',
    rc={'font.size': 10}
)

print("\nGenerating charts...")

# 1. Main Candlestick Chart with EMAs
ema9_plot = mpf.make_addplot(df['EMA9'], color='#f59e0b', width=1.5)
ema21_plot = mpf.make_addplot(df['EMA21'], color='#ef4444', width=1.5)

fig, axes = mpf.plot(
    df, type='candle', style=s,
    title='Bitcoin (BTC/USDT) - 120 Days (Real Binance Data)',
    ylabel='Price (USDT)', ylabel_lower='Volume (BTC)',
    volume=True, addplot=[ema9_plot, ema21_plot],
    figsize=(14, 8), returnfig=True, tight_layout=True
)
fig.savefig('/root/btc-daily-report/chart_main_real.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("✅ Main chart: chart_main_real.png")

# 2. Bollinger Bands Chart
bb_upper = mpf.make_addplot(df['BB_Upper'], color='#8b5cf6', width=1.5)
bb_lower = mpf.make_addplot(df['BB_Lower'], color='#8b5cf6', width=1.5)
bb_middle = mpf.make_addplot(df['BB_Middle'], color='#64748b', width=1)

fig, axes = mpf.plot(
    df, type='candle', style=s,
    title='Bitcoin with Bollinger Bands (20, 2) - Real Data',
    ylabel='Price (USDT)', volume=False,
    addplot=[bb_upper, bb_lower, bb_middle],
    figsize=(14, 6), returnfig=True, tight_layout=True
)
fig.savefig('/root/btc-daily-report/chart_bb_real.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("✅ Bollinger Bands: chart_bb_real.png")

# 3. VWAP Chart
vwap_plot = mpf.make_addplot(df['VWAP'], color='#06b6d4', width=2)

fig, axes = mpf.plot(
    df, type='candle', style=s,
    title='Bitcoin with VWAP - Real Data',
    ylabel='Price (USDT)', volume=False,
    addplot=[vwap_plot],
    figsize=(14, 6), returnfig=True, tight_layout=True
)
fig.savefig('/root/btc-daily-report/chart_vwap_real.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("✅ VWAP: chart_vwap_real.png")

# 4. RSI Chart
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(df.index, df['RSI'], color='#f59e0b', linewidth=2)
ax.axhline(y=70, color='#ef4444', linestyle='--', alpha=0.7, label='Overbought (70)')
ax.axhline(y=30, color='#10b981', linestyle='--', alpha=0.7, label='Oversold (30)')
ax.axhline(y=50, color='#64748b', linestyle='-', alpha=0.3)
ax.fill_between(df.index, 30, 70, alpha=0.1, color='#64748b')
ax.set_title('RSI (Relative Strength Index) - Real Data', fontsize=14, fontweight='bold')
ax.set_ylabel('RSI', fontsize=12)
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
fig.savefig('/root/btc-daily-report/chart_rsi_real.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("✅ RSI: chart_rsi_real.png")

# 5. MACD Chart
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(df.index, df['MACD'], color='#3b82f6', linewidth=2, label='MACD')
ax.plot(df.index, df['MACD_Signal'], color='#f59e0b', linewidth=2, label='Signal')
ax.axhline(y=0, color='#64748b', linestyle='--', alpha=0.5)
ax.set_title('MACD (12, 26, 9) - Real Data', fontsize=14, fontweight='bold')
ax.set_ylabel('MACD', fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
fig.savefig('/root/btc-daily-report/chart_macd_real.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("✅ MACD: chart_macd_real.png")

print("\n🎉 All TradingView-quality charts generated with REAL data!")
print(f"   Actual price range: ${df['Low'].min():,.0f} - ${df['High'].max():,.0f}")
print(f"   Current price: ${df['Close'].iloc[-1]:,.0f}")
