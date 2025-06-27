# Just a quick script I used to understand price data behavior and think about signals.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data/abra_price.csv")

df['mid_price'] = (df['bid_price_1'] + df['ask_price_1']) / 2

window = 50
k = 2

df['sma'] = df['mid_price'].rolling(window).mean()
df['std'] = df['mid_price'].rolling(window).std()
df['upper_band'] = df['sma'] + k * df['std']
df['lower_band'] = df['sma'] - k * df['std']
df['zscore'] = (df['mid_price'] - df['sma']) / df['std']
df['volatility'] = df['std'] / df['sma']

df['signal'] = np.where(df['zscore'] > 1, -1, 
                        np.where(df['zscore'] < -1, 1, 0))

df['pnl'] = df['signal'].shift(1) * (df['mid_price'].diff())

plt.figure(figsize=(14, 10))

plt.subplot(3, 1, 1)
plt.plot(df['mid_price'], label='Mid Price')
plt.plot(df['sma'], label='SMA')
plt.plot(df['upper_band'], label='Upper Band', linestyle='--', color='r')
plt.plot(df['lower_band'], label='Lower Band', linestyle='--', color='g')
plt.title("Mid Price & Bollinger Bands")
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(df['zscore'], label='Z-score', color='purple')
plt.axhline(1, color='red', linestyle='--')
plt.axhline(-1, color='green', linestyle='--')
plt.title("Z-Score of Mid Price")
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(df['volatility'], label='Relative Volatility', color='orange')
plt.title("Volatility Over Time")
plt.legend()

plt.tight_layout()
plt.show()
