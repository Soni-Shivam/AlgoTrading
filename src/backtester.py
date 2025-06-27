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

class Backtester:
    POSITION_LIMIT = 50

    def __init__(self, price_csv_path, trades_csv_path, trader):
        self.price_csv_path = price_csv_path
        self.trades_csv_path = trades_csv_path
        self.trader = trader

        self.prices = {}  # timestamp -> price row dict
        self.trades = {}  # timestamp -> list of Trade

        # Legacy tracking (for backward compatibility)
        self.position = 0
        self.pnl = 0

        # New enhanced tracking
        self.position_tracker = PositionTracker()
        self.orderbook = OrderBook()

        # For tracking history for plotting
        self.position_history = []
        self.pnl_history = []
        self.realized_pnl_history = []
        self.unrealized_pnl_history = []
        self.total_pnl_history = []
        self.mid_price_history = []
        self.timestamps = []

    def load_data(self):
        # Load price data
        with open(self.price_csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ts = int(row['timestamp'])
                self.prices[ts] = row

        # Load trades data
        with open(self.trades_csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ts = int(row['timestamp'])
                trade = Trade(ts, int(row['price']), int(row['quantity']))
                self.trades.setdefault(ts, []).append(trade)

    def get_mid_price(self):
        """Calculate current mid price from orderbook"""
        if not self.orderbook.buy_orders or not self.orderbook.sell_orders:
            return 10000  # fallback price
        
        best_bid = max(self.orderbook.buy_orders.keys())
        best_ask = min(self.orderbook.sell_orders.keys())
        return (best_bid + best_ask) / 2

    def match_orders(self, orders: List[Order], market_trades: List[Trade]):
        for order in orders:
            qty_to_fill = abs(order.quantity)
            filled = 0
            
            # Enforce position limits
            if order.quantity > 0:
                max_allowed = self.POSITION_LIMIT - self.position
                if max_allowed <= 0:
                    continue
                qty_to_fill = min(qty_to_fill, max_allowed)
            else:
                max_allowed = self.position + self.POSITION_LIMIT
                if max_allowed <= 0:
                    continue
                qty_to_fill = min(qty_to_fill, max_allowed)

            if order.quantity > 0:
                # Buy order matching sell orders
                sell_prices = sorted(p for p in self.orderbook.sell_orders if p <= order.price)
                for sp in sell_prices:
                    avail = self.orderbook.sell_orders[sp]
                    fill = min(qty_to_fill - filled, avail)
                    if fill <= 0:
                        continue
                    
                    # Update legacy tracking
                    filled += fill
                    self.position += fill
                    self.pnl -= fill * sp
                    
                    # Update enhanced tracking
                    self.position_tracker.add_trade(fill, sp)
                    
                    self.orderbook.sell_orders[sp] -= fill
                    if self.orderbook.sell_orders[sp] == 0:
                        del self.orderbook.sell_orders[sp]
                    if filled == qty_to_fill:
                        break

                # Match market trades with price <= order price
                for trade in market_trades[:]:
                    if trade.price <= order.price and filled < qty_to_fill:
                        fill = min(qty_to_fill - filled, trade.quantity)
                        
                        # Update legacy tracking
                        filled += fill
                        self.position += fill
                        self.pnl -= fill * trade.price
                        
                        # Update enhanced tracking
                        self.position_tracker.add_trade(fill, trade.price)
                        
                        trade.quantity -= fill
                        if trade.quantity == 0:
                            market_trades.remove(trade)
                        if filled == qty_to_fill:
                            break

            else:
                # Sell order matching buy orders
                buy_prices = sorted((p for p in self.orderbook.buy_orders if p >= order.price), reverse=True)
                for bp in buy_prices:
                    avail = self.orderbook.buy_orders[bp]
                    fill = min(qty_to_fill - filled, avail)
                    if fill <= 0:
                        continue
                    
                    # Update legacy tracking
                    filled += fill
                    self.position -= fill
                    self.pnl += fill * bp
                    
                    # Update enhanced tracking
                    self.position_tracker.add_trade(-fill, bp)
                    
                    self.orderbook.buy_orders[bp] -= fill
                    if self.orderbook.buy_orders[bp] == 0:
                        del self.orderbook.buy_orders[bp]
                    if filled == qty_to_fill:
                        break

                # Match market trades with price >= order price
                for trade in market_trades[:]:
                    if trade.price >= order.price and filled < qty_to_fill:
                        fill = min(qty_to_fill - filled, trade.quantity)
                        
                        # Update legacy tracking
                        filled += fill
                        self.position -= fill
                        self.pnl += fill * trade.price
                        
                        # Update enhanced tracking
                        self.position_tracker.add_trade(-fill, trade.price)
                        
                        trade.quantity -= fill
                        if trade.quantity == 0:
                            market_trades.remove(trade)
                        if filled == qty_to_fill:
                            break

    def run(self):
        self.load_data()
        timestamps = sorted(self.prices.keys())

        for ts in timestamps:
            self.orderbook.update_from_price_row(self.prices[ts])
            market_trades = self.trades.get(ts, [])

            state = type("State", (), {})()
            state.timestamp = ts
            state.order_depth = self.orderbook
            orders_dict = self.trader.run(state, self.position)
            orders = orders_dict.get("PRODUCT", [])

            self.match_orders(orders, market_trades)

            # Calculate current mid price and unrealized PnL
            mid_price = self.get_mid_price()
            realized_pnl = self.position_tracker.realized_pnl
            unrealized_pnl = self.position_tracker.get_unrealized_pnl(mid_price)
            total_pnl = realized_pnl + unrealized_pnl

            # Track history for plotting
            self.timestamps.append(ts)
            self.position_history.append(self.position)
            self.pnl_history.append(self.pnl)  # Legacy cash-flow PnL
            self.realized_pnl_history.append(realized_pnl)
            self.unrealized_pnl_history.append(unrealized_pnl)
            self.total_pnl_history.append(total_pnl)
            self.mid_price_history.append(mid_price)

        # Auto-clear position at last timestamp (simplified version)
        if self.position != 0:
            print(f"Auto-clearing position of {self.position} at last timestamp {timestamps[-1]}")
            last_mid_price = self.get_mid_price()
            
            # Clear position at mid price
            self.position_tracker.add_trade(-self.position, last_mid_price)
            self.pnl += self.position * last_mid_price if self.position < 0 else -self.position * last_mid_price
            self.position = 0
            
            # Update final history
            final_realized_pnl = self.position_tracker.realized_pnl
            final_unrealized_pnl = self.position_tracker.get_unrealized_pnl(last_mid_price)
            
            self.timestamps.append(timestamps[-1] + 1)
            self.position_history.append(0)
            self.pnl_history.append(self.pnl)
            self.realized_pnl_history.append(final_realized_pnl)
            self.unrealized_pnl_history.append(final_unrealized_pnl)
            self.total_pnl_history.append(final_realized_pnl + final_unrealized_pnl)
            self.mid_price_history.append(last_mid_price)

        print(f"Final position after autoclear: {self.position}")
        print(f"Final Legacy PnL: {self.pnl}")
        print(f"Final Realized PnL: {self.position_tracker.realized_pnl:.2f}")
        print(f"Final Unrealized PnL: {self.position_tracker.get_unrealized_pnl(self.get_mid_price()):.2f}")
        print(f"Final Total PnL: {self.position_tracker.realized_pnl + self.position_tracker.get_unrealized_pnl(self.get_mid_price()):.2f}")

    def get_detailed_summary(self):
        """Get detailed trading summary with realized/unrealized breakdown"""
        if not self.timestamps:
            return "No trading data available"
        
        final_realized = self.realized_pnl_history[-1] if self.realized_pnl_history else 0
        final_unrealized = self.unrealized_pnl_history[-1] if self.unrealized_pnl_history else 0
        final_total = self.total_pnl_history[-1] if self.total_pnl_history else 0
        
        max_realized = max(self.realized_pnl_history) if self.realized_pnl_history else 0
        min_realized = min(self.realized_pnl_history) if self.realized_pnl_history else 0
        
        return f"""
ENHANCED PnL BREAKDOWN:
├── Realized PnL: {final_realized:.2f} (from closed positions)
├── Unrealized PnL: {final_unrealized:.2f} (from open positions) 
├── Total PnL: {final_total:.2f}
├── Peak Realized PnL: {max_realized:.2f}
└── Lowest Realized PnL: {min_realized:.2f}

POSITION SUMMARY:
├── Final Position: {self.position}
├── Legacy Cash PnL: {self.pnl:.2f}
└── Enhanced Total PnL: {final_total:.2f}
"""