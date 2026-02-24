#!/usr/bin/env python3
"""
Generate 120 days of BTC data for charts
"""

import json
import random
import math

random.seed(42)

# Generate 120 days of realistic BTC data
days = 120
base_prices = []
price = 72000  # Starting price ~3 months ago

for i in range(days):
    # Add randomness with some trend changes
    if i < 40:
        # First month: slight uptrend then flat
        change = random.uniform(-600, 800)
    elif i < 80:
        # Second month: downtrend begins
        change = random.uniform(-900, 400) - 200
    else:
        # Third month: continued downtrend
        change = random.uniform(-800, 500) - 300
    
    price += change
    price = max(58000, min(78000, price))  # keep in realistic range
    base_prices.append(round(price, 2))

# Ensure we end near current price
base_prices[-1] = 66217
base_prices[-2] = 66500
base_prices[-3] = 66800

def generate_ema(prices, period):
    k = 2 / (period + 1)
    ema = [prices[0]]
    for i in range(1, len(prices)):
        ema.append(prices[i] * k + ema[-1] * (1 - k))
    return ema

def generate_bb(prices, period=20, std_dev=2):
    bb = []
    for i in range(len(prices)):
        if i < period - 1:
            bb.append({'upper': prices[i], 'middle': prices[i], 'lower': prices[i]})
        else:
            slice_prices = prices[i-period+1:i+1]
            avg = sum(slice_prices) / period
            variance = sum((p - avg) ** 2 for p in slice_prices) / period
            std = math.sqrt(variance)
            bb.append({
                'upper': avg + std_dev * std,
                'middle': avg,
                'lower': avg - std_dev * std
            })
    return bb

def generate_rsi(prices, period=14):
    rsi = []
    for i in range(len(prices)):
        if i < period:
            rsi.append(50)
        else:
            gains = losses = 0
            for j in range(i-period+1, i+1):
                change = prices[j] - prices[j-1]
                if change > 0:
                    gains += change
                else:
                    losses += abs(change)
            avg_gain = gains / period
            avg_loss = losses / period
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
    return rsi

def generate_macd(prices, fast=12, slow=26, signal=9):
    def ema(data, period):
        k = 2 / (period + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(data[i] * k + result[-1] * (1 - k))
        return result
    
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal)
    
    return {'macd': macd_line, 'signal': signal_line}

def generate_volume(prices):
    volume = []
    for i, price in enumerate(prices):
        base_vol = random.uniform(25000, 55000)
        if i > 0:
            change = abs(price - prices[i-1])
            if change > 500:
                base_vol *= 1.4
        volume.append(round(base_vol))
    return volume

def generate_vwap(prices, volume):
    vwap = []
    cumulative_tpv = 0
    cumulative_vol = 0
    for price, vol in zip(prices, volume):
        cumulative_tpv += price * vol
        cumulative_vol += vol
        vwap.append(cumulative_tpv / cumulative_vol)
    return vwap

# Calculate all indicators
ema9 = generate_ema(base_prices, 9)
ema21 = generate_ema(base_prices, 21)
bb = generate_bb(base_prices)
rsi = generate_rsi(base_prices)
macd_data = generate_macd(base_prices)
volume = generate_volume(base_prices)
vwap = generate_vwap(base_prices, volume)

# Generate dates
def get_date_label(i):
    if i < 30:
        return f'Nov {i+1}'
    elif i < 61:
        return f'Dec {i-29}'
    elif i < 92:
        return f'Jan {i-60}'
    else:
        return f'Feb {i-91}'

dates = [get_date_label(i) for i in range(days)]

# Save data
chart_data = {
    'prices': base_prices,
    'ema9': ema9,
    'ema21': ema21,
    'bb_upper': [b['upper'] for b in bb],
    'bb_middle': [b['middle'] for b in bb],
    'bb_lower': [b['lower'] for b in bb],
    'rsi': rsi,
    'macd': macd_data['macd'],
    'macd_signal': macd_data['signal'],
    'volume': volume,
    'vwap': vwap,
    'dates': dates,
    'days': days
}

with open('/root/btc-daily-report/chart_data_120.json', 'w') as f:
    json.dump(chart_data, f, indent=2)

print(f"Generated {days} days of chart data")
print(f"Price range: ${min(base_prices):,.0f} - ${max(base_prices):,.0f}")
print(f"Current RSI: {rsi[-1]:.1f}")
print(f"Current MACD: {macd_data['macd'][-1]:.0f}")
