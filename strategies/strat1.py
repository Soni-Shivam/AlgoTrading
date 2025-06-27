from src.backtester import Order, OrderBook
from typing import List
import numpy as np

class Trader:
    def __init__(self):
        self.mid_prices = []
        self.window = 20
        self.k = 1.5
        self.position_limit = 20
        self.base_order_size = 5

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

        buy_vol = sum(order_depth.buy_orders.values())
        sell_vol = sum(order_depth.sell_orders.values())
        imbalance = (buy_vol - sell_vol) / (buy_vol + sell_vol + 1e-6)

        volatility = np.std(np.diff(prices))
        volatility = max(0.05, volatility)
        scaled_size = min(self.base_order_size * 2, int(self.base_order_size / volatility))

        if imbalance > 0.2:
            long_bias = 1.5
        elif imbalance < -0.2:
            long_bias = 0.5
        else:
            long_bias = 1.0

        if zscore < -self.k and current_position < self.position_limit:
            qty = int(min(self.position_limit - current_position, scaled_size * long_bias))
            orders.append(Order("PRODUCT", best_bid, qty))

        elif zscore > self.k and current_position > -self.position_limit:
            qty = int(min(self.position_limit + current_position, scaled_size / long_bias))
            orders.append(Order("PRODUCT", best_ask - 1, -qty))

        elif abs(zscore) < 0.2:
            if current_position > 0:
                orders.append(Order("PRODUCT", best_ask, -min(current_position, self.base_order_size)))
            elif current_position < 0:
                orders.append(Order("PRODUCT", best_bid, min(-current_position, self.base_order_size)))

        result["PRODUCT"] = orders
        return result
