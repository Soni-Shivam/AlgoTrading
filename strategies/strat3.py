# Fourth attempt — added a momentum filter to avoid fighting strong trends.
# Mean reversion only when price movement is weak. Smarter? Maybe.

from src.backtester import Order, OrderBook
from typing import List
import numpy as np

class Trader:
    def __init__(self):
        self.prices = []
        self.z_window = 30
        self.momentum_window = 10
        self.z_threshold = 1.2
        self.momentum_threshold = 0.2
        self.position_limit = 50
        self.order_size = 5

    def run(self, state, current_position):
        result = {}
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        # Sorted book
        sorted_buys = sorted(order_depth.buy_orders.items(), key=lambda x: -x[0])
        sorted_sells = sorted(order_depth.sell_orders.items(), key=lambda x: x[0])

        if not sorted_buys or not sorted_sells:
            result["PRODUCT"] = []
            return result

        best_bid = sorted_buys[0][0]
        best_ask = sorted_sells[0][0]
        mid_price = (best_bid + best_ask) / 2
        self.prices.append(mid_price)

        # Require full history
        if len(self.prices) < self.z_window:
            result["PRODUCT"] = []
            return result

        self.prices = self.prices[-max(self.z_window, self.momentum_window):]
        prices_np = np.array(self.prices)

        # --- Z-score (mean reversion) ---
        z_prices = prices_np[-self.z_window:]
        sma = np.mean(z_prices)
        std = np.std(z_prices)
        zscore = (mid_price - sma) / std if std != 0 else 0

        # --- Momentum filter ---
        momentum = (mid_price - self.prices[-self.momentum_window]) / self.prices[-self.momentum_window]

        # --- Entry Logic: Mean Reversion Only if Momentum is Weak ---
        if zscore < -self.z_threshold and momentum < self.momentum_threshold and current_position < self.position_limit:
            orders.append(Order("PRODUCT", best_bid, min(self.order_size, self.position_limit - current_position)))

        elif zscore > self.z_threshold and momentum > -self.momentum_threshold and current_position > -self.position_limit:
            orders.append(Order("PRODUCT", best_ask - 1, -min(self.order_size, self.position_limit + current_position)))

        # --- Exit Logic ---
        elif abs(zscore) < 0.2:
            if current_position > 0:
                orders.append(Order("PRODUCT", best_ask, -min(self.order_size, current_position)))
            elif current_position < 0:
                orders.append(Order("PRODUCT", best_bid, min(self.order_size, -current_position)))

        result["PRODUCT"] = orders
        return result
 