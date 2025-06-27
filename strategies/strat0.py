# Mean Reversion Trading Strategy using Z-Score of Mid-Price
# ----------------------------------------------------------
# First try at a mean reversion strategy.
# Buy low, sell high based on Z-score from mid-price.
# Exit when price goes back to average. Let’s see if it works!
from src.backtester import Order, OrderBook
from typing import List
import numpy as np

class Trader:
    def __init__(self):
        self.mid_prices = []
        self.window = 20
        self.k = 1.5
        self.position_limit = 20
        self.order_size = 5

    def run(self, state, current_position):
        result = {}
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        sorted_buys = sorted(order_depth.buy_orders.items(), key=lambda x: -x[0])
        sorted_sells = sorted(order_depth.sell_orders.items(), key=lambda x: x[0])

        if not sorted_buys or not sorted_sells:
            result["PRODUCT"] = []
            return result

        best_bid = sorted_buys[0][0]
        best_ask = sorted_sells[0][0]
        mid_price = (best_bid + best_ask) / 2

        self.mid_prices.append(mid_price)
        if len(self.mid_prices) < self.window:
            result["PRODUCT"] = []
            return result

        self.mid_prices = self.mid_prices[-self.window:]
        prices = np.array(self.mid_prices)

        sma = np.mean(prices)
        std = np.std(prices)
        zscore = (mid_price - sma) / std if std != 0 else 0

        if zscore < -self.k and current_position < self.position_limit:
            orders.append(Order("PRODUCT", best_bid, self.order_size))

        elif zscore > self.k and current_position > -self.position_limit:
            orders.append(Order("PRODUCT", best_ask - 1, -self.order_size))

        elif abs(zscore) < 0.2:
            if current_position > 0:
                orders.append(Order("PRODUCT", best_ask, -self.order_size))
            elif current_position < 0:
                orders.append(Order("PRODUCT", best_bid, self.order_size))

        result["PRODUCT"] = orders
        return result

