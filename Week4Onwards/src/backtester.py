import csv
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Order:
    symbol: str
    price: int
    quantity: int

@dataclass
class Trade:
    timestamp: int
    price: int
    quantity: int

class OrderBook:
    def __init__(self):
        self.buy_orders: Dict[int, int] = {}  # price -> volume
        self.sell_orders: Dict[int, int] = {}

    def update_from_price_row(self, row):
        self.buy_orders.clear()
        self.sell_orders.clear()
        
        for i in range(1, 4):
            bp = int(row[f"bid_price_{i}"]) if row[f"bid_price_{i}"] else None
            bv = int(row[f"bid_volume_{i}"]) if row[f"bid_volume_{i}"] else 0
            if bp is not None:
                self.buy_orders[bp] = bv

            ap = int(row[f"ask_price_{i}"]) if row[f"ask_price_{i}"] else None
            av = int(row[f"ask_volume_{i}"]) if row[f"ask_volume_{i}"] else 0
            if ap is not None:
                self.sell_orders[ap] = av

class PositionTracker:
    """Tracks realized and unrealized PnL using FIFO accounting"""
    
    def __init__(self):
        self.position = 0
        self.realized_pnl = 0.0
        self.long_queue = []  # [(quantity, price), ...] for long positions
        self.short_queue = []  # [(quantity, price), ...] for short positions

    def add_trade(self, quantity, price):
        """Add a trade and calculate realized PnL using FIFO"""
        if quantity > 0:  # Buy trade
            self._process_buy(quantity, price)
        else:  # Sell trade
            self._process_sell(abs(quantity), price)
        
        self.position += quantity

    def _process_buy(self, quantity, price):
        """Process a buy trade"""
        remaining_qty = quantity
        
        # First, close any short positions (realize profit/loss)
        while remaining_qty > 0 and self.short_queue:
            short_qty, short_price = self.short_queue[0]
            if remaining_qty >= short_qty:
                # Close entire short position
                self.realized_pnl += short_qty * (short_price - price)
                remaining_qty -= short_qty
                self.short_queue.pop(0)
            else:
                # Partially close short position
                self.realized_pnl += remaining_qty * (short_price - price)
                self.short_queue[0] = (short_qty - remaining_qty, short_price)
                remaining_qty = 0
        
        # Add remaining quantity as new long position
        if remaining_qty > 0:
            self.long_queue.append((remaining_qty, price))

    def _process_sell(self, quantity, price):
        """Process a sell trade"""
        remaining_qty = quantity
        
        # First, close any long positions (realize profit/loss)
        while remaining_qty > 0 and self.long_queue:
            long_qty, long_price = self.long_queue[0]
            if remaining_qty >= long_qty:
                # Close entire long position
                self.realized_pnl += long_qty * (price - long_price)
                remaining_qty -= long_qty
                self.long_queue.pop(0)
            else:
                # Partially close long position
                self.realized_pnl += remaining_qty * (price - long_price)
                self.long_queue[0] = (long_qty - remaining_qty, long_price)
                remaining_qty = 0
        
        # Add remaining quantity as new short position
        if remaining_qty > 0:
            self.short_queue.append((remaining_qty, price))

    def get_unrealized_pnl(self, current_price):
        """Calculate unrealized PnL at current market price"""
        unrealized = 0.0
        
        # Unrealized PnL from long positions
        for qty, entry_price in self.long_queue:
            unrealized += qty * (current_price - entry_price)
        
        # Unrealized PnL from short positions
        for qty, entry_price in self.short_queue:
            unrealized += qty * (entry_price - current_price)
        
        return unrealized

    def get_average_cost(self):
        """Get average cost/price of current position"""
        if self.position == 0:
            return 0.0
        
        total_cost = 0.0
        total_qty = 0
        
        for qty, price in self.long_queue:
            total_cost += qty * price
            total_qty += qty
        
        for qty, price in self.short_queue:
            total_cost += qty * price  # Short positions have "negative cost"
            total_qty += qty
        
        return total_cost / total_qty if total_qty > 0 else 0.0

class MultiProductBacktester:
    POSITION_LIMIT = {
        "SHINX": 50,
        "LUXRAY": 250,
        "JOLTEON": 350,
        "ASH": 60,
        "MISTY": 100,
        "SUDOWOODO": 50,
        "ABRA": 50,
        "DROWZEE": 50
    }

    def __init__(self, product_data_paths: Dict[str, Dict[str, str]], trader):
        """
        Initialize backtester for multiple products
        
        Args:
            product_data_paths: Dict of {product_name: {'price_csv': path, 'trades_csv': path}}
            trader: Trading strategy instance
        """
        self.product_data_paths = product_data_paths
        self.trader = trader
        self.products = list(product_data_paths.keys())
        
        # Per-product data storage
        self.prices = {}  # {product: {timestamp: price_row_dict}}
        self.trades = {}  # {product: {timestamp: [Trade, ...]}}
        self.orderbooks = {}  # {product: OrderBook}
        self.position_trackers = {}  # {product: PositionTracker}
        
        # Per-product legacy tracking (for backward compatibility)
        self.positions = {}  # {product: position}
        self.pnls = {}  # {product: pnl}
        
        # Per-product history tracking
        self.position_histories = {}  # {product: [positions]}
        self.pnl_histories = {}  # {product: [pnls]}
        self.realized_pnl_histories = {}  # {product: [realized_pnls]}
        self.unrealized_pnl_histories = {}  # {product: [unrealized_pnls]}
        self.total_pnl_histories = {}  # {product: [total_pnls]}
        self.mid_price_histories = {}  # {product: [mid_prices]}
        
        # Overall tracking
        self.timestamps = []
        self.overall_pnl_history = []
        self.overall_realized_pnl_history = []
        self.overall_unrealized_pnl_history = []
        
        # Initialize per-product structures
        for product in self.products:
            self.prices[product] = {}
            self.trades[product] = {}
            self.orderbooks[product] = OrderBook()
            self.position_trackers[product] = PositionTracker()
            self.positions[product] = 0
            self.pnls[product] = 0
            self.position_histories[product] = []
            self.pnl_histories[product] = []
            self.realized_pnl_histories[product] = []
            self.unrealized_pnl_histories[product] = []
            self.total_pnl_histories[product] = []
            self.mid_price_histories[product] = []

    def load_data(self):
        """Load price and trades data for all products"""
        for product in self.products:
            price_path = self.product_data_paths[product]['price_csv']
            trades_path = self.product_data_paths[product]['trades_csv']
            
            # Load price data
            with open(price_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    ts = int(row['timestamp'])
                    self.prices[product][ts] = row

            # Load trades data
            with open(trades_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    ts = int(row['timestamp'])
                    trade = Trade(ts, int(row['price']), int(row['quantity']))
                    self.trades[product].setdefault(ts, []).append(trade)

    def get_mid_price(self, product):
        """Calculate current mid price from orderbook for specific product"""
        orderbook = self.orderbooks[product]
        if not orderbook.buy_orders or not orderbook.sell_orders:
            return 10000  # fallback price

        best_bid = max(orderbook.buy_orders.keys())
        best_ask = min(orderbook.sell_orders.keys())
        return (best_bid + best_ask) / 2

    def match_orders(self, orders: List[Order], timestamp, max_pos):
        """Match orders for all products at given timestamp"""
        # Group orders by product
        orders_by_product = {}
        for order in orders:
            orders_by_product.setdefault(order.symbol, []).append(order)
        
        # Process orders for each product
        for product, product_orders in orders_by_product.items():
            if product not in self.products:
                continue
                
            market_trades = self.trades[product].get(timestamp, [])
            self._match_product_orders(product, product_orders, market_trades, max_pos)

    def _match_product_orders(self, product, orders: List[Order], market_trades: List[Trade], max_pos):
        """Match orders for a specific product"""
        orderbook = self.orderbooks[product]
        position_tracker = self.position_trackers[product]
        
        for order in orders:
            qty_to_fill = abs(order.quantity)
            filled = 0

            # Enforce position limits
            current_position = self.positions[product]
            if order.quantity > 0:
                if max_pos:
                    max_allowed = max_pos - current_position
                else:
                    max_allowed = self.POSITION_LIMIT[product] - current_position
                if max_allowed <= 0:
                    continue
                qty_to_fill = min(qty_to_fill, max_allowed)
            else:
                if max_pos:
                    max_allowed = current_position + max_pos
                else:
                    max_allowed = current_position + self.POSITION_LIMIT[product]
                if max_allowed <= 0:
                    continue
                qty_to_fill = min(qty_to_fill, max_allowed)

            if order.quantity > 0:
                # Buy order matching sell orders
                sell_prices = sorted(p for p in orderbook.sell_orders if p <= order.price)
                for sp in sell_prices:
                    avail = orderbook.sell_orders[sp]
                    fill = min(qty_to_fill - filled, avail)
                    if fill <= 0:
                        continue

                    # Update legacy tracking
                    filled += fill
                    self.positions[product] += fill
                    self.pnls[product] -= fill * sp

                    # Update enhanced tracking
                    position_tracker.add_trade(fill, sp)
                    orderbook.sell_orders[sp] -= fill
                    if orderbook.sell_orders[sp] == 0:
                        del orderbook.sell_orders[sp]

                    if filled == qty_to_fill:
                        break

                # Match market trades with price <= order price
                for trade in market_trades[:]:
                    if trade.price <= order.price and filled < qty_to_fill:
                        fill = min(qty_to_fill - filled, trade.quantity)
                        
                        # Update legacy tracking
                        filled += fill
                        self.positions[product] += fill
                        self.pnls[product] -= fill * trade.price

                        # Update enhanced tracking
                        position_tracker.add_trade(fill, trade.price)
                        trade.quantity -= fill
                        if trade.quantity == 0:
                            market_trades.remove(trade)

                        if filled == qty_to_fill:
                            break

            else:
                # Sell order matching buy orders
                buy_prices = sorted((p for p in orderbook.buy_orders if p >= order.price), reverse=True)
                for bp in buy_prices:
                    avail = orderbook.buy_orders[bp]
                    fill = min(qty_to_fill - filled, avail)
                    if fill <= 0:
                        continue

                    # Update legacy tracking
                    filled += fill
                    self.positions[product] -= fill
                    self.pnls[product] += fill * bp

                    # Update enhanced tracking
                    position_tracker.add_trade(-fill, bp)
                    orderbook.buy_orders[bp] -= fill
                    if orderbook.buy_orders[bp] == 0:
                        del orderbook.buy_orders[bp]

                    if filled == qty_to_fill:
                        break

                # Match market trades with price >= order price
                for trade in market_trades[:]:
                    if trade.price >= order.price and filled < qty_to_fill:
                        fill = min(qty_to_fill - filled, trade.quantity)
                        
                        # Update legacy tracking
                        filled += fill
                        self.positions[product] -= fill
                        self.pnls[product] += fill * trade.price

                        # Update enhanced tracking
                        position_tracker.add_trade(-fill, trade.price)
                        trade.quantity -= fill
                        if trade.quantity == 0:
                            market_trades.remove(trade)

                        if filled == qty_to_fill:
                            break

    def run(self):
        """Run the backtest simulation"""
        self.load_data()
        
        # Get all unique timestamps across all products
        all_timestamps = set()
        for product in self.products:
            all_timestamps.update(self.prices[product].keys())
        
        timestamps = sorted(all_timestamps)
        self.timestamps = timestamps

        for ts in timestamps:
            # Update orderbooks for all products
            for product in self.products:
                if ts in self.prices[product]:
                    self.orderbooks[product].update_from_price_row(self.prices[product][ts])

            # Create state object with all orderbooks
            state = type("State", (), {})()
            state.timestamp = ts
            state.order_depth = {product: self.orderbooks[product] for product in self.products}
            state.positions = self.positions

            # Get orders from trader
            orders_dict, max_pos = self.trader.run(state)
            
            # Flatten orders from all products
            all_orders = []
            for product_orders in orders_dict.values():
                all_orders.extend(product_orders)

            # Match orders
            self.match_orders(all_orders, ts, max_pos)

            # Calculate and track metrics for each product
            overall_realized_pnl = 0
            overall_unrealized_pnl = 0
            overall_total_pnl = 0
            
            for product in self.products:
                mid_price = self.get_mid_price(product)
                realized_pnl = self.position_trackers[product].realized_pnl
                unrealized_pnl = self.position_trackers[product].get_unrealized_pnl(mid_price)
                total_pnl = realized_pnl + unrealized_pnl

                # Track per-product history
                self.position_histories[product].append(self.positions[product])
                self.pnl_histories[product].append(self.pnls[product])
                self.realized_pnl_histories[product].append(realized_pnl)
                self.unrealized_pnl_histories[product].append(unrealized_pnl)
                self.total_pnl_histories[product].append(total_pnl)
                self.mid_price_histories[product].append(mid_price)
                
                # Accumulate overall metrics
                overall_realized_pnl += realized_pnl
                overall_unrealized_pnl += unrealized_pnl
                overall_total_pnl += total_pnl

            # Track overall history
            self.overall_realized_pnl_history.append(overall_realized_pnl)
            self.overall_unrealized_pnl_history.append(overall_unrealized_pnl)
            self.overall_pnl_history.append(overall_total_pnl)

        # Auto-clear positions at last timestamp
        if timestamps:
            last_ts = timestamps[-1]
            print(f"Auto-clearing all positions at last timestamp {last_ts}")
            
            for product in self.products:
                if self.positions[product] != 0:
                    print(f"Auto-clearing {product} position of {self.positions[product]}")
                    last_mid_price = self.get_mid_price(product)
                    
                    # Clear position at mid price
                    self.position_trackers[product].add_trade(-self.positions[product], last_mid_price)
                    self.pnls[product] += (self.positions[product] * last_mid_price 
                                         if self.positions[product] < 0 
                                         else -self.positions[product] * last_mid_price)
                    self.positions[product] = 0

            # Update final history after clearing
            overall_final_realized = sum(tracker.realized_pnl for tracker in self.position_trackers.values())
            overall_final_unrealized = sum(tracker.get_unrealized_pnl(self.get_mid_price(product)) 
                                         for product, tracker in self.position_trackers.items())
            
            self.timestamps.append(last_ts + 1)
            self.overall_realized_pnl_history.append(overall_final_realized)
            self.overall_unrealized_pnl_history.append(overall_final_unrealized)
            self.overall_pnl_history.append(overall_final_realized + overall_final_unrealized)
            
            for product in self.products:
                self.position_histories[product].append(0)
                self.pnl_histories[product].append(self.pnls[product])
                self.realized_pnl_histories[product].append(self.position_trackers[product].realized_pnl)
                self.unrealized_pnl_histories[product].append(
                    self.position_trackers[product].get_unrealized_pnl(self.get_mid_price(product))
                )
                self.total_pnl_histories[product].append(
                    self.position_trackers[product].realized_pnl + 
                    self.position_trackers[product].get_unrealized_pnl(self.get_mid_price(product))
                )
                self.mid_price_histories[product].append(self.get_mid_price(product))

        self._print_final_summary()

    def _print_final_summary(self):
        """Print comprehensive final summary"""
        print("\n" + "="*80)
        print("MULTI-PRODUCT BACKTEST SUMMARY")
        print("="*80)
        
        overall_realized = self.overall_realized_pnl_history[-1] if self.overall_realized_pnl_history else 0
        overall_total = self.overall_pnl_history[-1] if self.overall_pnl_history else 0
        
        print(f"\n OVERALL PERFORMANCE:")
        print(f"├── Total Realized PnL: ${overall_realized:.2f}")
        print(f"└── Total PnL: ${overall_total:.2f}")
        
        print(f"\n PER-PRODUCT BREAKDOWN:")
        for product in self.products:
            final_pos = self.positions[product]
            final_realized = (self.realized_pnl_histories[product][-1] 
                            if self.realized_pnl_histories[product] else 0)
            final_total = (self.total_pnl_histories[product][-1] 
                         if self.total_pnl_histories[product] else 0)
            
            print(f"├── {product}:")
            print(f"│   ├── Final Position: {final_pos}")
            print(f"│   ├── Realized PnL: ${final_realized:.2f}")
            print(f"│   └── Total PnL: ${final_total:.2f}")

    def get_detailed_summary(self):
        """Get detailed trading summary with per-product breakdown"""
        if not self.timestamps:
            return "No trading data available"

        summary = "\n" + "="*80 + "\n"
        summary += "MULTI-PRODUCT BACKTEST DETAILED SUMMARY\n"
        summary += "="*80 + "\n"

        # Overall metrics
        overall_realized = self.overall_realized_pnl_history[-1] if self.overall_realized_pnl_history else 0
        overall_total = self.overall_pnl_history[-1] if self.overall_pnl_history else 0
        
        summary += f"\n OVERALL PERFORMANCE:\n"
        summary += f"├── Total Realized PnL: ${overall_realized:.2f}\n"
        summary += f"├── Total PnL: ${overall_total:.2f}\n"
        summary += f"└── Products Traded: {len(self.products)}\n"

        # Per-product breakdown
        summary += f"\n DETAILED PER-PRODUCT ANALYSIS:\n"
        for i, product in enumerate(self.products):
            final_pos = self.positions[product]
            final_realized = (self.realized_pnl_histories[product][-1] 
                            if self.realized_pnl_histories[product] else 0)
            final_total = (self.total_pnl_histories[product][-1] 
                         if self.total_pnl_histories[product] else 0)
            max_realized = (max(self.realized_pnl_histories[product]) 
                          if self.realized_pnl_histories[product] else 0)
            min_realized = (min(self.realized_pnl_histories[product]) 
                          if self.realized_pnl_histories[product] else 0)
            
            connector = "├──" if i < len(self.products) - 1 else "└──"
            sub_connector = "│" if i < len(self.products) - 1 else " "
            
            summary += f"{connector} {product}:\n"
            summary += f"{sub_connector}   ├── Final Position: {final_pos}\n"
            summary += f"{sub_connector}   ├── Realized PnL: ${final_realized:.2f}\n"
            summary += f"{sub_connector}   ├── Total PnL: ${final_total:.2f}\n"
            summary += f"{sub_connector}   ├── Peak Realized PnL: ${max_realized:.2f}\n"
            summary += f"{sub_connector}   └── Lowest Realized PnL: ${min_realized:.2f}\n"

        return summary

# Backward compatibility class
class Backtester(MultiProductBacktester):
    """Single-product backtester for backward compatibility"""
    
    def __init__(self, price_csv_path, trades_csv_path, trader):
        product_data = {
            "PRODUCT": {
                "price_csv": price_csv_path,
                "trades_csv": trades_csv_path
            }
        }
        super().__init__(product_data, trader)
        
        # Legacy properties for backward compatibility
        self.price_csv_path = price_csv_path
        self.trades_csv_path = trades_csv_path
        
    @property
    def position(self):
        return self.positions.get("PRODUCT", 0)
    
    @property
    def pnl(self):
        return self.pnls.get("PRODUCT", 0)
    
    @property
    def position_tracker(self):
        return self.position_trackers.get("PRODUCT")
    
    @property
    def orderbook(self):
        return self.orderbooks.get("PRODUCT")
    
    @property
    def position_history(self):
        return self.position_histories.get("PRODUCT", [])
    
    @property
    def pnl_history(self):
        return self.pnl_histories.get("PRODUCT", [])
    
    @property
    def realized_pnl_history(self):
        return self.realized_pnl_histories.get("PRODUCT", [])
    
    @property
    def unrealized_pnl_history(self):
        return self.unrealized_pnl_histories.get("PRODUCT", [])
    
    @property
    def total_pnl_history(self):
        return self.total_pnl_histories.get("PRODUCT", [])
    
    @property
    def mid_price_history(self):
        return self.mid_price_histories.get("PRODUCT", [])