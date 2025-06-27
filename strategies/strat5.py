from src.backtester import Order, OrderBook
from typing import List
import numpy as np

class Trader:
    def __init__(self):
        self.prices = []
        self.z_window = 30
        self.vol_window = 20
        self.z_entry_threshold = 1.2
        self.z_exit_threshold = 0.2
        self.vol_spike_factor = 0.1
        self.position_limit = 50
        self.order_size = 5
        self.mm_spread = 2  # Market making spread from mid

    def run(self, state, current_position):
        result = {}
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth

        # Get best bid/ask
        sorted_buys = sorted(order_depth.buy_orders.items(), key=lambda x: -x[0])
        sorted_sells = sorted(order_depth.sell_orders.items(), key=lambda x: x[0])
        if not sorted_buys or not sorted_sells:
            result["PRODUCT"] = []
            return result

        best_bid = sorted_buys[0][0]
        best_ask = sorted_sells[0][0]
        mid_price = (best_bid + best_ask) / 2
        self.prices.append(mid_price)

        if len(self.prices) < max(self.z_window, self.vol_window):
            result["PRODUCT"] = []
            return result

        self.prices = self.prices[-max(self.z_window, self.vol_window):]
        prices_np = np.array(self.prices)

        # --- Z-score ---
        z_prices = prices_np[-self.z_window:]
        mean = np.mean(z_prices)
        std = np.std(z_prices)
        zscore = (mid_price - mean) / std if std != 0 else 0

        # --- Volatility Spike Detection ---
        vol_window_prices = prices_np[-self.vol_window:]
        rolling_std = np.std(vol_window_prices)
        recent_std = np.std(vol_window_prices[-5:])
        vol_spike = recent_std > self.vol_spike_factor * rolling_std

        traded = False

        # --- Mean Reversion Entry Logic ---
        if zscore < -self.z_entry_threshold and vol_spike and current_position < self.position_limit:
            qty = min(self.order_size, self.position_limit - current_position)
            orders.append(Order("PRODUCT", best_bid, qty))
            traded = True

        elif zscore > self.z_entry_threshold and vol_spike and current_position > -self.position_limit:
            qty = min(self.order_size, self.position_limit + current_position)
            orders.append(Order("PRODUCT", best_ask - 1, -qty))
            traded = True

        # --- Exit logic ---
        elif abs(zscore) < self.z_exit_threshold:
            if current_position > 0:
                qty = min(self.order_size, current_position)
                orders.append(Order("PRODUCT", best_ask, -qty))
                traded = True
            elif current_position < 0:
                qty = min(self.order_size, -current_position)
                orders.append(Order("PRODUCT", best_bid, qty))
                traded = True

        # --- Market Making Logic ---
        if not traded and abs(current_position) < self.position_limit:
            mm_bid = mid_price - self.mm_spread
            mm_ask = mid_price + self.mm_spread
            orders.append(Order("PRODUCT", mm_bid, self.order_size))
            orders.append(Order("PRODUCT", mm_ask, -self.order_size))

        result["PRODUCT"] = orders
        return result
