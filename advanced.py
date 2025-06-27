from src.backtester import Order, OrderBook
from typing import List
import numpy as np

class Trader:
    def __init__(self):
        # Internal memory of past mid-prices
        self.mid_prices = []

        # Parameters
        self.window = 20         # For rolling stats
        self.k = 2               # For Bollinger Bands
        self.vol_threshold = 0.002  # Volatility threshold for breakout
        self.position_limit = 20
        self.order_size = 5

    def run(self, state, current_position):
        result = {}
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        # Get sorted best bid and ask
        sorted_buys = sorted(order_depth.buy_orders.items(), key=lambda x: -x[0])
        sorted_sells = sorted(order_depth.sell_orders.items(), key=lambda x: x[0])

        if not sorted_buys or not sorted_sells:
            result["PRODUCT"] = []
            return result

        best_bid = sorted_buys[0][0]
        best_ask = sorted_sells[0][0]
        mid_price = (best_bid + best_ask) / 2

        # Update mid-price history
        self.mid_prices.append(mid_price)
        if len(self.mid_prices) < self.window:
            result["PRODUCT"] = []
            return result  # wait for enough data

        # Keep only the last 'window' prices
        self.mid_prices = self.mid_prices[-self.window:]
        prices = np.array(self.mid_prices)

        sma = np.mean(prices)
        std = np.std(prices)
        upper_band = sma + self.k * std
        lower_band = sma - self.k * std
        zscore = (mid_price - sma) / std if std != 0 else 0
        volatility = std / sma if sma != 0 else 0
        dzdt = zscore - ((prices[-2] - np.mean(prices[:-1])) / (np.std(prices[:-1]) + 1e-8))  # slope estimate

        signal = 0  # 0 = no trade, 1 = buy, -1 = sell

        """  # Mode 1: Mean Reversion
        if volatility < self.vol_threshold:
            if zscore < -1.5 and mid_price < lower_band:
                signal = 1  # Buy
            elif zscore > 1.5 and mid_price > upper_band:
                signal = -1  # Sell
        # Mode 2: Breakout
        elif volatility >= self.vol_threshold:
            if mid_price > upper_band and dzdt > 0:
                signal = 1  # Long breakout
            elif mid_price < lower_band and dzdt < 0:
                signal = -1  # Short breakout """

        if zscore < -1.5 and mid_price < lower_band:
            signal = 1  # Buy
        elif zscore > 1.5 and mid_price > upper_band:
            signal = -1  # Sell

        # Position control
        if signal == 1 and current_position < self.position_limit:
            price = best_ask + 1  # aggressive buy above ask
            orders.append(Order("PRODUCT", price, self.order_size))
        elif signal == -1 and current_position > -self.position_limit:
            price = best_bid - 1  # aggressive sell below bid
            orders.append(Order("PRODUCT", price, -self.order_size))

        result["PRODUCT"] = orders
        return result
