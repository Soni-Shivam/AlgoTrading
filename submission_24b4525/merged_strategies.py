from src.backtester import Order, OrderBook
from typing import List
import pandas as pd
import numpy as np
import statistics
import math

# Base Class
class BaseClass:
    def __init__(self, product_name, max_position):
        self.product_name = product_name
        self.max_position = max_position
    
    def get_orders(self, state, orderbook, position):
        """Override this method in product-specific strategies"""
        return []

class SudowoodoStrategy(BaseClass): # Inherit from Base Class
    def __init__(self):
        super().__init__("PRODUCT", 250) # Initialize using the init dunder from its Parent class
        self.fair_value = 4300
    
    def get_orders(self, state, orderbook, position):
        orders = []
        
        if not orderbook.buy_orders and not orderbook.sell_orders:
            return orders
        # LOGIC FROM THE NOTEBOOK SHARED ON NOTION FOR SUDOWOODO
        orders.append(Order(self.product_name, self.fair_value + 2, -10))
        orders.append(Order(self.product_name, self.fair_value - 2, 10))

        return orders

class Abra(BaseClass):
    def __init__(self):
        super().__init__("ABRA", 50)
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
class Ash(BaseClass):
    def __init__(self):
        super().__init__("ASH", 60)
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

class Jolteon(BaseClass):
    def __init__(self):
        super().__init__("JOLTEON", 350)
        self.prices = []
        self.lookback = 100
        self.entry_z = 2.0
        self.exit_z = 0.4
        self.stop_loss_z = 4
        self.base_qty = 9
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
            orders.append(Order(self.product_name, best_ask-1, -min(qty, self.max_position + position)))

        # Exit Mean Reversion
        elif abs(z_score) < self.exit_z:
            if position > 0:
                orders.append(Order(self.product_name, best_ask+1, -min(abs(position), qty)))
            elif position < 0:
                orders.append(Order(self.product_name, best_bid, min(abs(position), qty)))

        # Stop Loss
        elif abs(z_score) > self.stop_loss_z:
            if position > 0:
                orders.append(Order(self.product_name, best_bid, -abs(position)))
            elif position < 0:
                orders.append(Order(self.product_name, best_ask, abs(position)))

        # Market Making
        if not orders and abs(position) < self.max_position:
            orders.append(Order(self.product_name, mid_price - self.mm_spread, self.base_qty))
            orders.append(Order(self.product_name, mid_price + self.mm_spread, -self.base_qty))

        return orders

class LuxrayStrategy(BaseClass):
    def __init__(self):
        super().__init__("LUXRAY", 250)  
        self.prices = []
        self.z_window = 200           
        self.vol_window = 70         
        self.entry_z = 1.6              
        self.exit_z = 0.3         
        self.vol_spike_factor = 1.25   
        self.base_qty = 20             
        self.scale_qty = 20           
        self.mm_spread = 2     

    def get_orders(self, state, orderbook: OrderBook, position: int):
        orders = []

        # Skip if no valid book data
        if not orderbook.buy_orders or not orderbook.sell_orders:
            return orders

        # Get best bid/ask and mid-price
        best_bid = max(orderbook.buy_orders.keys())
        best_ask = min(orderbook.sell_orders.keys())
        mid_price = (best_bid + best_ask) / 2

        self.prices.append(mid_price)

        # Not enough data → No trades
        if len(self.prices) < max(self.z_window, self.vol_window):
            return orders

        # Keep only recent window
        self.prices = self.prices[-max(self.z_window, self.vol_window):]
        recent_prices = np.array(self.prices)

        # Calculate Z-score
        mean_price = np.mean(recent_prices[-self.z_window:])
        std_price = np.std(recent_prices[-self.z_window:])
        z_score = (mid_price - mean_price) / std_price if std_price != 0 else 0

        # Volatility spike detection
        roll_std = np.std(recent_prices[-self.vol_window:])
        recent_std = np.std(recent_prices[-5:])
        volatility_spike = recent_std > self.vol_spike_factor * roll_std

        # Dynamic position sizing
        qty = int(self.base_qty + self.scale_qty * abs(z_score))
        qty = min(qty, self.max_position)

        traded = False

        # Entry: Long signal (relaxing volatility spike for re-entry)
        if z_score < -self.entry_z and position < self.max_position:
            if volatility_spike or position < 0:  # Allow reversal without spike
                orders.append(Order(self.product_name, best_bid, min(qty, self.max_position - position)))
                traded = True

        # Entry: Short signal (relaxing volatility spike for re-entry)
        elif z_score > self.entry_z and position > -self.max_position:
            if volatility_spike or position > 0:  # Allow reversal without spike
                orders.append(Order(self.product_name, best_ask - 1, -min(qty, self.max_position + position)))
                traded = True

        # Exit: Mean reversion
        elif abs(z_score) < self.exit_z:
            exit_qty = min(qty, abs(position))
            if position > 0:
                orders.append(Order(self.product_name, best_ask, -exit_qty))
            elif position < 0:
                orders.append(Order(self.product_name, best_bid-1   , exit_qty))
            traded = True

        # Passive Market Making if no clear signal
        if not traded and abs(position) < self.max_position:
            orders.append(Order(self.product_name, mid_price - self.mm_spread, self.base_qty))
            orders.append(Order(self.product_name, mid_price + self.mm_spread, -self.base_qty))

        return orders   
    
class ShinxStrategy(BaseClass):
    def __init__(self):
        super().__init__("SHINX", 60)  
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

class NewDrowzeeStrategy(BaseClass):
    def __init__(self):
        super().__init__("PRODUCT", 60)  
        self.lookback = 50
        self.z_threshold = 3.00  
        self.exit_z = 2  
        self.prices = []
        self.base_order_size = 7
        self.scale_factor = 2
        self.market_spread = 2
        self.stop_loss_distance = 10  # Fixed stop-loss in price units

    def get_orders(self, state, orderbook, position):
        orders = []

        if not orderbook.buy_orders or not orderbook.sell_orders:
            return orders

        best_bid = max(orderbook.buy_orders.keys())
        best_ask = min(orderbook.sell_orders.keys())
        mid_price = (best_bid + best_ask) / 2

        self.prices.append(mid_price)

        if len(self.prices) < self.lookback:
            return self.market_make(best_bid, best_ask, position)

        recent_prices = self.prices[-self.lookback:]
        mean_price = statistics.mean(recent_prices)
        stddev_price = statistics.stdev(recent_prices)

        if stddev_price == 0:
            return self.market_make(best_bid, best_ask, position)

        z_score = (mid_price - mean_price) / stddev_price

        # Stop-Loss Logic
        if position > 0 and mid_price < mean_price - self.stop_loss_distance:
            orders.append(Order(self.product_name, best_bid, -position))
            return orders
        if position < 0 and mid_price > mean_price + self.stop_loss_distance:
            orders.append(Order(self.product_name, best_ask, abs(position)))
            return orders

        # Mean Reversion Entries/Exits
        dynamic_order_size = min(self.base_order_size + self.scale_factor * abs(z_score), self.max_position - abs(position))

        if z_score > self.z_threshold and position > -self.max_position:
            orders.append(Order(self.product_name, best_bid, -int(dynamic_order_size)))
        elif z_score < -self.z_threshold and position < self.max_position:
            orders.append(Order(self.product_name, best_ask, int(dynamic_order_size)))
        elif abs(z_score) < self.exit_z:
            if position > 0:
                orders.append(Order(self.product_name, best_ask, -min(int(dynamic_order_size), position)))
            elif position < 0:
                orders.append(Order(self.product_name, best_bid, min(int(dynamic_order_size), abs(position))))
        else:
            return self.market_make(best_bid, best_ask, position)

        return orders

    def market_make(self, best_bid, best_ask, position):
        mid_price = (best_bid + best_ask) / 2
        skew = 0.05 * position
        adjusted_mid = mid_price + skew

        bid_price = adjusted_mid - self.market_spread
        ask_price = adjusted_mid + self.market_spread

        remaining_capacity = self.max_position - abs(position)
        order_size = min(self.base_order_size, remaining_capacity)

        orders = []
        if remaining_capacity > 0:
            orders.append(Order(self.product_name, bid_price, order_size))
            orders.append(Order(self.product_name, ask_price, -order_size))

        return orders
class DrowzeeStrategy(BaseClass):
    def __init__(self):
        super().__init__("DROWZEE", 50)
        self.lookback = 50
        self.z_threshold = 3.75
        self.prices = []
    
    def get_orders(self, state, orderbook, position):
        orders = []
        if not orderbook.buy_orders and not orderbook.sell_orders:
            return orders
        
        best_ask = min(orderbook.sell_orders.keys()) if orderbook.sell_orders else None
        best_bid = max(orderbook.buy_orders.keys()) if orderbook.buy_orders else None
        mid_price = (best_ask + best_bid) // 2
        self.prices.append(mid_price)

        if len(self.prices) > self.lookback:
            mean_price = statistics.mean(self.prices[-self.lookback:])
            stddev_price = statistics.stdev(self.prices[-self.lookback:])
            z_score = (mid_price - mean_price) / stddev_price
            if z_score > self.z_threshold:
                orders.append(Order(self.product_name, best_bid, -self.max_position + position))
            elif z_score < -self.z_threshold:
                orders.append(Order(self.product_name, best_ask, self.max_position - position))
            else:
                return self.market_make(mid_price)
        elif len(self.prices) <= self.lookback:
            return self.market_make(mid_price)
        return orders
    
    def market_make(self, price):
        orders = []
        orders.append(Order(self.product_name, price - 1, 25))
        orders.append(Order(self.product_name, price + 1, -25))
        return orders

class Trader:
    MAX_LIMIT = 0 # for single product mode only, don't remove
    def __init__(self):
        self.strategies = {
            "SUDOWOODO": SudowoodoStrategy(),
            "DROWZEE": DrowzeeStrategy(), 
            "ABRA": Abra(),
            "ASH": Ash(),
            "JOLTEON": Jolteon(),
            "LUXRAY": LuxrayStrategy(),
            "SHINX": ShinxStrategy()
        }
    
    def run(self, state):
        result = {}
        positions = getattr(state, 'positions', {})
        if len(self.strategies) == 1: self.MAX_LIMIT= self.strategies["PRODUCT"].max_position # for single product mode only, don't remove

        for product, orderbook in state.order_depth.items():
            current_position = positions.get(product, 0)
            product_orders = self.strategies[product].get_orders(state, orderbook, current_position)
            result[product] = product_orders
        
        return result, self.MAX_LIMIT
