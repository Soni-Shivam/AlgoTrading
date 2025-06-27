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
        super().__init__("SUDOWOODO", 50) # Initialize using the init dunder from its Parent class
        self.fair_value = 10000
    
    def get_orders(self, state, orderbook, position):
        orders = []
        
        if not orderbook.buy_orders and not orderbook.sell_orders:
            return orders
        # LOGIC FROM THE NOTEBOOK SHARED ON NOTION FOR SUDOWOODO
        orders.append(Order(self.product_name, self.fair_value + 2, -10))
        orders.append(Order(self.product_name, self.fair_value - 2, 10))

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

class AbraStrategy(BaseClass):
    def __init__(self):
        super().__init__("ABRA", 50)
        self.prices = []
        self.lookback = 200
        self.z_threshold = 2.0
        self.z_mm_threshold = 0.3
        self.skew_factor = 0.1
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
                orders.append(Order(self.product_name, best_bid, -5))
            elif z_score < -self.z_threshold:
                orders.append(Order(self.product_name, best_ask, 5))
            elif abs(z_score) < self.z_mm_threshold:
                return self.market_make(mid_price, position)
        elif len(self.prices) <= self.lookback:
            return self.market_make(mid_price, position)
        return orders

    def market_make(self, mid_price, position):
        orders = []
        adjusted_mid_price = mid_price + self.skew_factor*position
        orders.append(Order(self.product_name, adjusted_mid_price - 2, 5))
        orders.append(Order(self.product_name, adjusted_mid_price + 2, -5))
        return orders

class Trader:
    def __init__(self):
        self.strategies = {
            "SUDOWOODO": SudowoodoStrategy(),
            "PRODUCT": DrowzeeStrategy(), 
            "ABRA": AbraStrategy()
        }
    
    def run(self, state):
        result = {}
        positions = getattr(state, 'positions', {})
        
        for product, orderbook in state.order_depth.items():
            current_position = positions.get(product, 0)
            product_orders = self.strategies[product].get_orders(state, orderbook, current_position)
            result[product] = product_orders
        
        return result
