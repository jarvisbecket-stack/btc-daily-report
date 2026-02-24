#!/usr/bin/env python3
"""
Generate SVG charts with 120 data points
"""

import json

with open('/root/btc-daily-report/chart_data_120.json', 'r') as f:
    data = json.load(f)

prices = data['prices']
ema9 = data['ema9']
ema21 = data['ema21']
bb_upper = data['bb_upper']
bb_lower = data['bb_lower']
rsi = data['rsi']
macd = data['macd']
macd_signal = data['macd_signal']
volume = data['volume']
vwap = data['vwap']
days = data['days']

def map_value(val, min_val, max_val, height):
    return height - ((val - min_val) / (max_val - min_val)) * height

def generate_path(values, width, height, min_val, max_val):
    points = []
    for i, val in enumerate(values):
        x = (i / (len(values) - 1)) * width
        y = map_value(val, min_val, max_val, height)
        points.append(f"{x:.1f},{y:.1f}")
    return "M" + " L".join(points)

# Chart dimensions
W, H = 380, 150

# EMA Chart SVG with 120 points
min_p, max_p = 55000, 78000
def to_path(vals): return generate_path(vals, W, H, min_p, max_p)

# Sample every point for 120 days (will be dense)
ema_svg = f'''<svg viewBox="0 0 400 200" style="width:100%;height:180px;">
  <!-- Grid lines -->
  <line x1="40" y1="20" x2="420" y2="20" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="70" x2="420" y2="70" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="120" x2="420" y2="120" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="170" x2="420" y2="170" stroke="#e2e8f0" stroke-width="1"/>
  
  <!-- Y-axis labels -->
  <text x="35" y="25" text-anchor="end" font-size="10" fill="#64748b">$75K</text>
  <text x="35" y="75" text-anchor="end" font-size="10" fill="#64748b">$70K</text>
  <text x="35" y="125" text-anchor="end" font-size="10" fill="#64748b">$65K</text>
  <text x="35" y="175" text-anchor="end" font-size="10" fill="#64748b">$60K</text>
  
  <!-- X-axis labels (4 months) -->
  <text x="40" y="195" text-anchor="middle" font-size="10" fill="#64748b">Nov 23</text>
  <text x="173" y="195" text-anchor="middle" font-size="10" fill="#64748b">Dec 23</text>
  <text x="306" y="195" text-anchor="middle" font-size="10" fill="#64748b">Jan 23</text>
  <text x="420" y="195" text-anchor="middle" font-size="10" fill="#64748b">Feb 23</text>
  
  <!-- Price Line (120 points) -->
  <path d="{to_path(prices)}" fill="none" stroke="#4f46e5" stroke-width="1.5" transform="translate(40,15)"/>
  
  <!-- EMA 9 -->
  <path d="{to_path(ema9)}" fill="none" stroke="#f59e0b" stroke-width="1.5" transform="translate(40,15)"/>
  
  <!-- EMA 21 -->
  <path d="{to_path(ema21)}" fill="none" stroke="#ef4444" stroke-width="1.5" transform="translate(40,15)"/>
  
  <!-- Current value -->
  <text x="420" y="{map_value(prices[-1], min_p, max_p, H)+15:.0f}" font-size="11" fill="#4f46e5" font-weight="600">${prices[-1]:,.0f}</text>
</svg>'''

# RSI Chart SVG
min_r, max_r = 20, 95
def to_rsi_path(vals): return generate_path(vals, W, H, min_r, max_r)

rsi_svg = f'''<svg viewBox="0 0 400 200" style="width:100%;height:180px;">
  <!-- Grid lines -->
  <line x1="40" y1="20" x2="420" y2="20" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="57" x2="420" y2="57" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="95" x2="420" y2="95" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="132" x2="420" y2="132" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="170" x2="420" y2="170" stroke="#e2e8f0" stroke-width="1"/>
  
  <!-- Overbought/Oversold lines -->
  <line x1="40" y1="33" x2="420" y2="33" stroke="#ef4444" stroke-width="1" stroke-dasharray="4,2"/>
  <line x1="40" y1="157" x2="420" y2="157" stroke="#10b981" stroke-width="1" stroke-dasharray="4,2"/>
  
  <!-- Y-axis labels -->
  <text x="35" y="25" text-anchor="end" font-size="10" fill="#64748b">70</text>
  <text x="35" y="62" text-anchor="end" font-size="10" fill="#64748b">60</text>
  <text x="35" y="100" text-anchor="end" font-size="10" fill="#64748b">50</text>
  <text x="35" y="137" text-anchor="end" font-size="10" fill="#64748b">40</text>
  <text x="35" y="175" text-anchor="end" font-size="10" fill="#64748b">30</text>
  
  <!-- X-axis labels -->
  <text x="40" y="195" text-anchor="middle" font-size="10" fill="#64748b">Nov 23</text>
  <text x="173" y="195" text-anchor="middle" font-size="10" fill="#64748b">Dec 23</text>
  <text x="306" y="195" text-anchor="middle" font-size="10" fill="#64748b">Jan 23</text>
  <text x="420" y="195" text-anchor="middle" font-size="10" fill="#64748b">Feb 23</text>
  
  <!-- RSI Line -->
  <path d="{to_rsi_path(rsi)}" fill="none" stroke="#f59e0b" stroke-width="1.5" transform="translate(40,10)"/>
  
  <!-- Current value -->
  <text x="420" y="{map_value(rsi[-1], min_r, max_r, H)+10:.0f}" font-size="11" fill="#f59e0b" font-weight="600">{rsi[-1]:.0f}</text>
</svg>'''

# MACD Chart SVG
min_m, max_m = -500, 2000
def to_macd_path(vals): return generate_path(vals, W, H, min_m, max_m)

macd_svg = f'''<svg viewBox="0 0 400 200" style="width:100%;height:180px;">
  <!-- Grid lines -->
  <line x1="40" y1="20" x2="420" y2="20" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="57" x2="420" y2="57" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="95" x2="420" y2="95" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="132" x2="420" y2="132" stroke="#e2e8f0" stroke-width="1"/>
  <line x1="40" y1="170" x2="420" y2="170" stroke="#e2e8f0" stroke-width="1"/>
  
  <!-- Zero line -->
  <line x1="40" y1="132" x2="420" y2="132" stroke="#64748b" stroke-width="1" stroke-dasharray="4,2"/>
  
  <!-- Y-axis labels -->
  <text x="35" y="25" text-anchor="end" font-size="10" fill="#64748b">+200</text>
  <text x="35" y="62" text-anchor="end" font-size="10" fill="#64748b">+100</text>
  <text x="35" y="100" text-anchor="end" font-size="10" fill="#64748b">0</text>
  <text x="35" y="137" text-anchor="end" font-size="10" fill="#64748b">-100</text>
  <text x="35" y="175" text-anchor="end" font-size="10" fill="#64748b">-200</text>
  
  <!-- X-axis labels -->
  <text x="40" y="195" text-anchor="middle" font-size="10" fill="#64748b">Nov 23</text>
  <text x="173" y="195" text-anchor="middle" font-size="10" fill="#64748b">Dec 23</text>
  <text x="306" y="195" text-anchor="middle" font-size="10" fill="#64748b">Jan 23</text>
  <text x="420" y="195" text-anchor="middle" font-size="10" fill="#64748b">Feb 23</text>
  
  <!-- MACD Lines -->
  <path d="{to_macd_path(macd)}" fill="none" stroke="#3b82f6" stroke-width="1.5" transform="translate(40,10)"/>
  <path d="{to_macd_path(macd_signal)}" fill="none" stroke="#f59e0b" stroke-width="1.5" transform="translate(40,10)"/>
  
  <!-- Current value -->
  <text x="420" y="{map_value(macd[-1], min_m, max_m, H)+10:.0f}" font-size="11" fill="#3b82f6" font-weight="600">{macd[-1]:.0f}</text>
</svg>'''

# Save SVG files
with open('/root/btc-daily-report/chart_ema_120.svg', 'w') as f:
    f.write(ema_svg)
with open('/root/btc-daily-report/chart_rsi_120.svg', 'w') as f:
    f.write(rsi_svg)
with open('/root/btc-daily-report/chart_macd_120.svg', 'w') as f:
    f.write(macd_svg)

print("120-day SVG charts generated:")
print("- chart_ema_120.svg")
print("- chart_rsi_120.svg") 
print("- chart_macd_120.svg")
