class ShinxStrategy(BaseClass):
    def __init__(self):
        super().__init__("PRODUCT", 60)  # Replace 'PRODUCT' with your actual product name
        self.lookback = 50
        self.z_threshold = 2.8
        self.stop_loss_distance = 20  # Stop-loss in price units
        self.prices = []

    def get_orders(self, state, orderbook, position):
        orders = []

        if not orderbook.buy_orders or not orderbook.sell_orders:
            return orders

        best_ask = min(orderbook.sell_orders.keys())
        best_bid = max(orderbook.buy_orders.keys())
        mid_price = (best_ask + best_bid) // 2

        
        self.prices.append(mid_price)

        if len(self.prices) > self.lookback:
            recent_prices = self.prices[-self.lookback:]
            mean_price = statistics.mean(recent_prices)
            stddev_price = statistics.stdev(recent_prices)

            if stddev_price == 0:
                return self.market_make(mid_price)

            z_score = (mid_price - mean_price) / stddev_price

            # Stop-Loss: Close positions if losses exceed threshold
            if position > 0 and mid_price < mean_price - self.stop_loss_distance:
                orders.append(Order(self.product_name, best_bid, -position))  # Exit long
                return orders

            if position < 0 and mid_price > mean_price + self.stop_loss_distance:
                orders.append(Order(self.product_name, best_ask, abs(position)))  # Exit short
                return orders

            # Entry Signals
            if z_score > self.z_threshold:
                orders.append(Order(self.product_name, best_bid, -self.max_position + position))
            elif z_score < -self.z_threshold:
                orders.append(Order(self.product_name, best_ask, self.max_position - position))
            else:
                return self.market_make(mid_price)

        else:
            return self.market_make(mid_price)

        return orders

    def market_make(self, price):
        orders = [
            Order(self.product_name, price - 1, 25),
            Order(self.product_name, price + 1, -25)
        ]
        return orders