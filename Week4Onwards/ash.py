class Ash(BaseClass):
    def __init__(self):
        super().__init__("PRODUCT", 60)
        self.prices = []
        self.lookback = 100
        self.entry_z = 1.95
        self.exit_z = 0.7
        self.stop_loss_z = 3.5
        self.base_qty = 39
        self.mm_spread = 1

    def get_orders(self, state, orderbook: OrderBook, position: int):
        orders = []

        if not orderbook.buy_orders or not orderbook.sell_orders:
            return orders

        best_bid = max(orderbook.buy_orders.keys())
        best_ask = min(orderbook.sell_orders.keys())
        mid_price = (best_bid + best_ask) / 2

        self.prices.append(mid_price)

        if len(self.prices) < self.lookback:
            return orders

        self.prices = self.prices[-self.lookback:]
        mean_price = np.mean(self.prices)
        std_price = np.std(self.prices)
        z_score = (mid_price - mean_price) / std_price if std_price != 0 else 0

        qty = min(self.base_qty + int(5 * abs(z_score)), self.max_position)

        # Entry Long
        if z_score < -self.entry_z and position < self.max_position:
            orders.append(Order(self.product_name, best_bid+1, min(qty, self.max_position - position)))

        # Entry Short
        elif z_score > self.entry_z and position > -self.max_position:
            orders.append(Order(self.product_name, best_ask-3, -min(qty, self.max_position + position)))

        # Exit Mean Reversion
        elif abs(z_score) < self.exit_z:
            if position > 0:
                orders.append(Order(self.product_name, best_ask+1, -min(abs(position), qty)))
            elif position < 0:
                orders.append(Order(self.product_name, best_bid, min(abs(position), qty)))

        # Stop Loss
        elif abs(z_score) > self.stop_loss_z:
            if position > 0:
                orders.append(Order(self.product_name, best_bid-1, -abs(position)))
            elif position < 0:
                orders.append(Order(self.product_name, best_ask-1, abs(position)))

        # Market Making
        if not orders and abs(position) < self.max_position:
            orders.append(Order(self.product_name, mid_price-1, self.base_qty))
            orders.append(Order(self.product_name, mid_price+3, -self.base_qty))

        return orders