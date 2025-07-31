class Abra(BaseClass):
    def __init__(self):
        super().__init__("PRODUCT", 50)
        self.prices = []
        self.z_window = 30
        self.vol_window = 20
        self.entry_z = 1.2
        self.exit_z = 0.2
        self.vol_spike_factor = 0.1
        self.base_qty = 10
        self.scale_qty = 10
        self.mm_spread = 2

    def get_orders(self, state, orderbook: OrderBook, position: int):
        orders = []

        if not orderbook.buy_orders or not orderbook.sell_orders:
            return orders

        best_bid = max(orderbook.buy_orders.keys())
        best_ask = min(orderbook.sell_orders.keys())
        mid_price = (best_bid + best_ask) / 2

        self.prices.append(mid_price)

        if len(self.prices) < max(self.z_window, self.vol_window):
            return orders

        self.prices = self.prices[-max(self.z_window, self.vol_window):]
        recent_prices = np.array(self.prices)

        mean_price = np.mean(recent_prices[-self.z_window:])
        std_price = np.std(recent_prices[-self.z_window:])
        z_score = (mid_price - mean_price) / std_price if std_price != 0 else 0

        roll_std = np.std(recent_prices[-self.vol_window:])
        recent_std = np.std(recent_prices[-5:])
        vol_spike = recent_std > self.vol_spike_factor * roll_std

        qty = min(int(self.base_qty + self.scale_qty * abs(z_score)), self.max_position)

        traded = False

        if z_score < -self.entry_z and vol_spike and position < self.max_position:
            buy_qty = min(qty, self.max_position - position)
            orders.append(Order(self.product_name, best_bid, buy_qty))
            traded = True

        elif z_score > self.entry_z and vol_spike and position > -self.max_position:
            sell_qty = min(qty, self.max_position + position)
            orders.append(Order(self.product_name, best_ask - 1, -sell_qty))
            traded = True

        elif abs(z_score) < self.exit_z:
            exit_qty = min(qty, abs(position))
            if position > 0:
                orders.append(Order(self.product_name, best_ask, -exit_qty))
                traded = True
            elif position < 0:
                orders.append(Order(self.product_name, best_bid, exit_qty))
                traded = True

        if not traded and abs(position) < self.max_position:
            orders.append(Order(self.product_name, mid_price - self.mm_spread, self.base_qty))
            orders.append(Order(self.product_name, mid_price + self.mm_spread, -self.base_qty))

        return orders
