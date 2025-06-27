from src.backtester import Order, OrderBook
from typing import List
import numpy as np

class Trader:
    def __init__(self):
        self.data = []
        self.z_win = 30
        self.vol_win = 20
        self.entry_z = 1.2
        self.exit_z = 0.2
        self.vol_factor = 0.1
        self.limit = 50
        self.base_qty = 10
        self.scale = 10
        self.spread = 2

    def run(self, state, position):
        result = {}
        orders: List[Order] = []
        book: OrderBook = state.order_depth

        buys = sorted(book.buy_orders.items(), key=lambda x: -x[0])
        sells = sorted(book.sell_orders.items(), key=lambda x: x[0])

        if not buys or not sells:
            result["PRODUCT"] = []
            return result

        bid = buys[0][0]
        ask = sells[0][0]
        mid = (bid + ask) / 2
        self.data.append(mid)

        if len(self.data) < max(self.z_win, self.vol_win):
            result["PRODUCT"] = []
            return result

        self.data = self.data[-max(self.z_win, self.vol_win):]
        arr = np.array(self.data)

        mean = np.mean(arr[-self.z_win:])
        std = np.std(arr[-self.z_win:])
        z = (mid - mean) / std if std != 0 else 0

        # just checking if recent volatility is spiking
        roll_std = np.std(arr[-self.vol_win:])
        recent_std = np.std(arr[-5:])
        is_spike = recent_std > self.vol_factor * roll_std

        traded = False
        qty = int(self.base_qty + self.scale * abs(z))
        qty = min(qty, self.limit)

        if z < -self.entry_z and is_spike and position < self.limit:
            orders.append(Order("PRODUCT", bid, min(qty, self.limit - position)))
            traded = True

        elif z > self.entry_z and is_spike and position > -self.limit:
            orders.append(Order("PRODUCT", ask - 1, -min(qty, self.limit + position)))
            traded = True

        elif abs(z) < self.exit_z:
            q = min(qty, abs(position))
            if position > 0:
                orders.append(Order("PRODUCT", ask, -q))
            elif position < 0:
                orders.append(Order("PRODUCT", bid, q))
            traded = True

        if not traded and abs(position) < self.limit:
            orders.append(Order("PRODUCT", mid - self.spread, self.base_qty))
            orders.append(Order("PRODUCT", mid + self.spread, -self.base_qty))

        result["PRODUCT"] = orders
        return result
