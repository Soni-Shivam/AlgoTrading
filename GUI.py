import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import importlib.util
import traceback
import threading
import webbrowser
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
import numpy as np
from src.backtester import MultiProductBacktester, Backtester

class ModernMultiProductBacktesterGUI:
    def __init__(self, root):
        self.root = root
        root.title("Advanced Multi-Product Backtester Pro")
        root.geometry("1400x900")
        
        # Configure dark theme
        self.setup_dark_theme()
        
        self.product_data = {}  # {product_name: {'price_file': path, 'trades_file': path}}
        self.algo_file = ""
        self.backtester = None
        self.is_multi_product = False
        
        # Create main layout
        self.create_widgets()

    def setup_dark_theme(self):
        """Configure dark theme colors and styles"""
        self.colors = {
            'bg_primary': '#1e1e1e',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3d3d3d',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'accent': '#007acc',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336'
        }

        # Configure root
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button style
        style.configure('Dark.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       focuscolor='none',
                       relief='flat')
        style.map('Dark.TButton',
                 background=[('active', self.colors['accent']),
                           ('pressed', self.colors['bg_secondary'])])
        
        # Configure frame style
        style.configure('Dark.TFrame',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        # Configure label style
        style.configure('Dark.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        style.configure('Header.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Arial', 12, 'bold'))
        
        # Configure progressbar
        style.configure('Dark.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_secondary'])

    def create_widgets(self):
        """Create and layout all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Header
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🚀 Advanced Multi-Product Backtester Pro",
                               style='Header.TLabel')
        title_label.pack()

        # Mode selection
        mode_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        mode_frame.pack(fill='x', pady=(0, 20))
        
        mode_label = ttk.Label(mode_frame, text="🔧 Trading Mode", style='Header.TLabel')
        mode_label.pack(anchor='w')
        
        mode_buttons_frame = ttk.Frame(mode_frame, style='Dark.TFrame')
        mode_buttons_frame.pack(fill='x', pady=(10, 0))
        
        self.single_mode_btn = ttk.Button(mode_buttons_frame, text=" Single Product Mode",
                                         command=self.set_single_mode, style='Dark.TButton')
        self.single_mode_btn.pack(side='left', padx=(0, 10))
        
        self.multi_mode_btn = ttk.Button(mode_buttons_frame, text="📈 Multi-Product Mode",
                                        command=self.set_multi_mode, style='Dark.TButton')
        self.multi_mode_btn.pack(side='left')

        # Product management section
        self.products_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        self.products_frame.pack(fill='x', pady=(0, 20))
        
        products_label = ttk.Label(self.products_frame, text="📦 Product Management", style='Header.TLabel')
        products_label.pack(anchor='w')

        # Product controls frame
        product_controls_frame = ttk.Frame(self.products_frame, style='Dark.TFrame')
        product_controls_frame.pack(fill='x', pady=(10, 0))

        self.add_product_btn = ttk.Button(product_controls_frame, text="➕ Add Product",
                                         command=self.add_product, style='Dark.TButton',
                                         state='disabled')
        self.add_product_btn.pack(side='left', padx=(0, 10))

        self.remove_product_btn = ttk.Button(product_controls_frame, text="➖ Remove Product",
                                            command=self.remove_product, style='Dark.TButton',
                                            state='disabled')
        self.remove_product_btn.pack(side='left')

        # Products list frame with scrollbar
        self.products_list_frame = tk.Frame(self.products_frame, bg=self.colors['bg_primary'])
        self.products_list_frame.pack(fill='both', expand=True, pady=(10, 0))

        # Create treeview for products
        self.products_tree = ttk.Treeview(self.products_list_frame, 
                                         columns=('Price File', 'Trades File'), 
                                         show='tree headings',
                                         height=6)
        self.products_tree.heading('#0', text='Product', anchor='w')
        self.products_tree.heading('Price File', text='Price Data', anchor='w')
        self.products_tree.heading('Trades File', text='Trades Data', anchor='w')
        
        self.products_tree.column('#0', width=150)
        self.products_tree.column('Price File', width=300)
        self.products_tree.column('Trades File', width=300)

        products_scrollbar = ttk.Scrollbar(self.products_list_frame, orient='vertical', 
                                          command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=products_scrollbar.set)
        
        self.products_tree.pack(side='left', fill='both', expand=True)
        products_scrollbar.pack(side='right', fill='y')

        # Strategy section
        strategy_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        strategy_frame.pack(fill='x', pady=(0, 20))
        
        strategy_label = ttk.Label(strategy_frame, text="🧠 Strategy Configuration", style='Header.TLabel')
        strategy_label.pack(anchor='w')

        strategy_buttons_frame = ttk.Frame(strategy_frame, style='Dark.TFrame')
        strategy_buttons_frame.pack(fill='x', pady=(10, 0))

        self.algo_btn = ttk.Button(strategy_buttons_frame, text="🧠 Load Strategy",
                                  command=self.load_algo, style='Dark.TButton')
        self.algo_btn.pack(side='left', padx=(0, 10))

        # Run button
        self.run_btn = ttk.Button(strategy_buttons_frame, text="🚀 Run Backtest",
                                 command=self.run_backtest_threaded, style='Dark.TButton')
        self.run_btn.pack(side='left', padx=(20, 0))

        # Progress bar
        self.progress = ttk.Progressbar(strategy_buttons_frame, style='Dark.Horizontal.TProgressbar',
                                       mode='indeterminate')
        self.progress.pack(side='right', padx=(10, 0))

        # Status section
        status_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        status_frame.pack(fill='x', pady=(0, 20))
        
        status_label = ttk.Label(status_frame, text="📋 Status & Logs", style='Header.TLabel')
        status_label.pack(anchor='w')

        # Output text with scrollbar
        text_frame = tk.Frame(status_frame, bg=self.colors['bg_primary'])
        text_frame.pack(fill='x', pady=(10, 0))
        
        self.output_text = tk.Text(text_frame, height=8, width=80,
                                  bg=self.colors['bg_secondary'],
                                  fg=self.colors['text_primary'],
                                  insertbackground=self.colors['text_primary'],
                                  selectbackground=self.colors['accent'],
                                  font=('Consolas', 9),
                                  relief='flat',
                                  borderwidth=1)
        
        scrollbar = tk.Scrollbar(text_frame, bg=self.colors['bg_tertiary'])
        scrollbar.pack(side='right', fill='y')
        self.output_text.pack(side='left', fill='both', expand=True)
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)

        # Results section
        results_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        results_frame.pack(fill='both', expand=True)
        
        results_label = ttk.Label(results_frame, text="📈 Interactive Results", style='Header.TLabel')
        results_label.pack(anchor='w')

        # Results buttons
        viz_buttons_frame = ttk.Frame(results_frame, style='Dark.TFrame')
        viz_buttons_frame.pack(fill='x', pady=(10, 0))

        self.interactive_btn = ttk.Button(viz_buttons_frame, text=" Open Interactive Dashboard",
                                         command=self.open_interactive_plot, style='Dark.TButton',
                                         state='disabled')
        self.interactive_btn.pack(side='left', padx=(0, 10))

        # self.summary_btn = ttk.Button(viz_buttons_frame, text="📋 Performance Summary",
        #                              command=self.show_summary, style='Dark.TButton',
        #                              state='disabled')
        # self.summary_btn.pack(side='left', padx=(0, 10))

        self.export_btn = ttk.Button(viz_buttons_frame, text="💾 Export Results",
                                    command=self.export_results, style='Dark.TButton',
                                    state='disabled')
        self.export_btn.pack(side='left')

        # Quick stats frame
        self.stats_frame = ttk.Frame(results_frame, style='Dark.TFrame')
        self.stats_frame.pack(fill='x', pady=(10, 0))
        
        self.quick_stats_label = ttk.Label(self.stats_frame, text=" Run a backtest to see results",
                                          style='Dark.TLabel')
        self.quick_stats_label.pack(anchor='w')

        # Status labels
        self.create_status_labels(strategy_frame)

        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Initial log message
        self.log_message("🌟 Welcome to Advanced Multi-Product Backtester Pro!")
        self.log_message("💡 Select trading mode and configure your products to get started.")
        self.log_message("⌨️ Keyboard shortcuts: Ctrl+R (Run), Ctrl+S (Summary)")

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        self.root.bind('<Control-r>', lambda e: self.run_backtest_threaded())
        self.root.bind('<Control-s>', lambda e: self.show_summary() if self.backtester else None)
        self.root.bind('<Control-i>', lambda e: self.open_interactive_plot() if self.backtester else None)
        self.root.bind('<F5>', lambda e: self.run_backtest_threaded())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def create_status_labels(self, parent):
        """Create file status indicators"""
        status_frame = ttk.Frame(parent, style='Dark.TFrame')
        status_frame.pack(fill='x', pady=(10, 0))

        self.algo_status = ttk.Label(status_frame, text="❌ Strategy: Not loaded",
                                    style='Dark.TLabel')
        self.algo_status.pack(anchor='w')

    def set_single_mode(self):
        """Set single product mode"""
        self.is_multi_product = False
        self.product_data.clear()
        self.refresh_products_display()
        
        self.add_product_btn.config(state='disabled')
        self.remove_product_btn.config(state='disabled')
        
        # Add default single product
        self.add_single_product()
        
        self.log_message("🔧 Switched to Single Product Mode", 'success')

    def set_multi_mode(self):
        """Set multi-product mode"""
        self.is_multi_product = True
        self.product_data.clear()
        self.refresh_products_display()
        
        self.add_product_btn.config(state='normal')
        self.remove_product_btn.config(state='normal')
        
        self.log_message("🔧 Switched to Multi-Product Mode", 'success')

    def add_single_product(self):
        """Add single product for backward compatibility"""
        product_name = "PRODUCT"
        
        # Load price file
        price_file = filedialog.askopenfilename(
            title="Select Price Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not price_file:
            return
            
        # Load trades file
        trades_file = filedialog.askopenfilename(
            title="Select Trades Data CSV", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not trades_file:
            return
            
        self.product_data[product_name] = {
            'price_file': price_file,
            'trades_file': trades_file
        }
        
        self.refresh_products_display()
        self.log_message(f"✅ Single product configured successfully", 'success')

    def add_product(self):
        """Add a new product for multi-product mode"""
        if not self.is_multi_product:
            return
            
        # Get product name
        product_dialog = tk.Toplevel(self.root)
        product_dialog.title("Add Product")
        product_dialog.geometry("400x150")
        product_dialog.configure(bg=self.colors['bg_primary'])
        product_dialog.transient(self.root)
        product_dialog.grab_set()
        
        # Center the dialog
        product_dialog.update_idletasks()
        x = (product_dialog.winfo_screenwidth() // 2) - (product_dialog.winfo_width() // 2)
        y = (product_dialog.winfo_screenheight() // 2) - (product_dialog.winfo_height() // 2)
        product_dialog.geometry(f"+{x}+{y}")
        
        tk.Label(product_dialog, text="Enter Product Name:", 
                bg=self.colors['bg_primary'], fg=self.colors['text_primary']).pack(pady=10)
        
        product_name_var = tk.StringVar()
        entry = tk.Entry(product_dialog, textvariable=product_name_var, width=30)
        entry.pack(pady=5)
        entry.focus()
        
        result = {'name': None}
        
        def on_ok():
            name = product_name_var.get().strip().upper()
            if name and name not in self.product_data:
                result['name'] = name
                product_dialog.destroy()
            elif name in self.product_data:
                messagebox.showerror("Duplicate Product", f"Product '{name}' already exists!")
            else:
                messagebox.showerror("Invalid Name", "Please enter a valid product name!")
        
        def on_cancel():
            product_dialog.destroy()
        
        button_frame = tk.Frame(product_dialog, bg=self.colors['bg_primary'])
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=on_ok, 
                 bg=self.colors['bg_tertiary'], fg=self.colors['text_primary']).pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel,
                 bg=self.colors['bg_tertiary'], fg=self.colors['text_primary']).pack(side='left', padx=5)
        
        # Bind Enter key
        product_dialog.bind('<Return>', lambda e: on_ok())
        product_dialog.bind('<Escape>', lambda e: on_cancel())
        
        product_dialog.wait_window()
        
        if not result['name']:
            return
            
        product_name = result['name']
        
        # Load price file
        price_file = filedialog.askopenfilename(
            title=f"Select Price Data CSV for {product_name}",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not price_file:
            return
            
        # Load trades file
        trades_file = filedialog.askopenfilename(
            title=f"Select Trades Data CSV for {product_name}",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not trades_file:
            return
            
        self.product_data[product_name] = {
            'price_file': price_file,
            'trades_file': trades_file
        }
        
        self.refresh_products_display()
        self.log_message(f"✅ Product '{product_name}' added successfully", 'success')

    def remove_product(self):
        """Remove selected product"""
        if not self.is_multi_product:
            return
            
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a product to remove")
            return
            
        item = selection[0]
        product_name = self.products_tree.item(item, 'text')
        
        if messagebox.askyesno("Confirm Removal", f"Remove product '{product_name}'?"):
            del self.product_data[product_name]
            self.refresh_products_display()
            self.log_message(f"🗑️ Product '{product_name}' removed", 'warning')

    def refresh_products_display(self):
        """Refresh the products display"""
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
            
        # Add current products
        for product_name, data in self.product_data.items():
            price_file = data['price_file'].split('/')[-1] if data['price_file'] else "Not loaded"
            trades_file = data['trades_file'].split('/')[-1] if data['trades_file'] else "Not loaded"
            
            self.products_tree.insert('', 'end', text=product_name, 
                                     values=(price_file, trades_file))

    def load_algo(self):
        self.algo_file = filedialog.askopenfilename(
            title="Select Strategy Python File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )

        if self.algo_file:
            self.log_message(f"Strategy loaded: {self.algo_file.split('/')[-1]}", 'success')
            self.algo_status.config(text=f"✅ Strategy: {self.algo_file.split('/')[-1]}")

    def log_message(self, message, level='info'):
        """Add timestamped message to output text"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == 'error':
            icon = "❌"
        elif level == 'success':
            icon = "✅"
        elif level == 'warning':
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        formatted_message = f"[{timestamp}] {icon} {message}\n"
        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update()

    def run_backtest_threaded(self):
        """Run backtest in separate thread to prevent GUI freezing"""
        if not self.product_data or not self.algo_file:
            messagebox.showerror("Missing Configuration", 
                               "Please configure products and load strategy first")
            return

        # Start progress animation
        self.progress.start(10)
        self.run_btn.config(state='disabled')

        # Run in separate thread
        thread = threading.Thread(target=self.run_backtest)
        thread.daemon = True
        thread.start()

    def run_backtest(self):
        """Execute the backtest"""
        try:
            self.log_message("🚀 Starting backtest execution...")

            # Load strategy module
            spec = importlib.util.spec_from_file_location("strategy", self.algo_file)
            strategy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(strategy)
            trader = strategy.Trader()

            self.log_message("✅ Strategy module loaded successfully")

            # Prepare product data paths
            product_data_paths = {}
            for product_name, data in self.product_data.items():
                product_data_paths[product_name] = {
                    'price_csv': data['price_file'],
                    'trades_csv': data['trades_file']
                }

            # Initialize appropriate backtester
            if self.is_multi_product or len(self.product_data) > 1:
                self.backtester = MultiProductBacktester(product_data_paths, trader)
                self.log_message(f" Running multi-product backtest for {len(self.product_data)} products...")
            else:
                # Single product - use backward compatible backtester
                product_name = list(self.product_data.keys())[0]
                data = self.product_data[product_name]
                self.backtester = Backtester(data['price_file'], data['trades_file'], trader)
                self.log_message(" Running single-product backtest...")

            # Run backtest
            self.backtester.run()

            # Log results
            self.log_message("🎉 Backtest completed successfully!", 'success')
            
            if isinstance(self.backtester, MultiProductBacktester) and len(self.backtester.products) > 1:
                # Multi-product results
                overall_pnl = (self.backtester.overall_pnl_history[-1] 
                             if self.backtester.overall_pnl_history else 0)
                self.log_message(f"💰 Overall Final PnL: {overall_pnl:.2f}")
                
                for product in self.backtester.products:
                    product_pnl = (self.backtester.total_pnl_histories[product][-1] 
                                 if self.backtester.total_pnl_histories[product] else 0)
                    self.log_message(f" {product} PnL: {product_pnl:.2f}")
            else:
                # Single product results
                self.log_message(f" Final Position: {self.backtester.position}")
                self.log_message(f"💰 Final PnL: {(self.backtester.total_pnl_histories['PRODUCT'][-1] if self.backtester.total_pnl_histories['PRODUCT'] else 0)}")

            # Enable visualization buttons
            self.interactive_btn.config(state='normal')
            # self.summary_btn.config(state='normal')
            self.export_btn.config(state='normal')

            # Update quick stats
            self.update_quick_stats()

        except Exception as e:
            self.log_message("❌ Error during backtest execution:", 'error')
            self.log_message(str(e), 'error')
            self.log_message(traceback.format_exc())

        finally:
            # Stop progress animation and re-enable button
            self.progress.stop()
            self.run_btn.config(state='normal')

    def update_quick_stats(self):
        """Update the quick stats display"""
        if not self.backtester:
            return

        if isinstance(self.backtester, MultiProductBacktester) and len(self.backtester.products) > 1:
            # Multi-product stats
            overall_pnl = (self.backtester.overall_pnl_history[-1] 
                         if self.backtester.overall_pnl_history else 0)
            max_pnl = max(self.backtester.overall_pnl_history) if self.backtester.overall_pnl_history else 0
            min_pnl = min(self.backtester.overall_pnl_history) if self.backtester.overall_pnl_history else 0
            
            stats_text = f"💰 Overall PnL: ${overall_pnl:,.2f} | 📦 Products: {len(self.backtester.products)} | 📈 Max: ${max_pnl:,.2f} | 📉 Min: ${min_pnl:,.2f}"
        else:
            # Single product stats
            final_pnl = (self.backtester.total_pnl_histories['PRODUCT'][-1] if self.backtester.total_pnl_histories['PRODUCT'] else 0)
            final_position = self.backtester.position
            max_pnl = max(self.backtester.realized_pnl_history) if self.backtester.realized_pnl_history else 0
            min_pnl = min(self.backtester.realized_pnl_history) if self.backtester.realized_pnl_history else 0
            
            stats_text = f"💰 Final PnL: ${final_pnl:,.2f} |  Position: {final_position} | 📈 Max: ${max_pnl:,.2f} | 📉 Min: ${min_pnl:,.2f}"

        self.quick_stats_label.config(text=stats_text)

    def export_results(self):
        """Export backtest results to CSV"""
        if not self.backtester:
            messagebox.showerror("No Data", "Please run a backtest first")
            return

        try:
            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                title="Save Results As",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if not file_path:
                return

            if isinstance(self.backtester, MultiProductBacktester) and len(self.backtester.products) > 1:
                # Multi-product export
                data = {'Timestamp': self.backtester.timestamps}
                
                # Add overall metrics
                data['Overall_PnL'] = self.backtester.overall_pnl_history
                data['Overall_Realized_PnL'] = self.backtester.overall_realized_pnl_history
                data['Overall_Unrealized_PnL'] = self.backtester.overall_unrealized_pnl_history
                
                # Add per-product metrics
                for product in self.backtester.products:
                    data[f'{product}_Position'] = self.backtester.position_histories[product]
                    data[f'{product}_PnL'] = self.backtester.total_pnl_histories[product]
                    data[f'{product}_Realized_PnL'] = self.backtester.realized_pnl_histories[product]
                    data[f'{product}_Unrealized_PnL'] = self.backtester.unrealized_pnl_histories[product]
                
                df = pd.DataFrame(data)
            else:
                # Single product export
                df = pd.DataFrame({
                    'Timestamp': self.backtester.timestamps,
                    'Position': self.backtester.position_history,
                    'PnL': self.backtester.realized_pnl_history
                })

            # Save to CSV
            df.to_csv(file_path, index=False)
            self.log_message(f"✅ Results exported to: {file_path.split('/')[-1]}", 'success')

        except Exception as e:
            self.log_message(f"❌ Error exporting results: {str(e)}", 'error')

    def open_interactive_plot(self):
        """Create and open interactive plotly dashboard"""
        if not self.backtester:
            messagebox.showerror("No Data", "Please run a backtest first")
            return

        try:
            self.log_message("🎨 Creating interactive dashboard...")

            if isinstance(self.backtester, MultiProductBacktester) and len(self.backtester.products) > 1:
                self._create_multi_product_plot()
            else:
                self._create_single_product_plot()

        except Exception as e:
            self.log_message(f"❌ Error creating dashboard: {str(e)}", 'error')

    def _create_multi_product_plot(self):
        """Create multi-product interactive plot"""
        timestamps = self.backtester.timestamps
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            vertical_spacing=0.08,
            subplot_titles=('Overall Performance', 'Per-Product PnL', 'Per-Product Positions'),
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}],
                   [{"secondary_y": False}]]
        )

        # Overall PnL plot
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=self.backtester.overall_pnl_history,
                mode='lines',
                name='Overall PnL',
                line=dict(color='#00d4ff', width=3),
                hovertemplate='Timestamp: %{x}<br>Overall PnL: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # Per-product PnL plots
        colors = ['#ffa500', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7']
        for i, product in enumerate(self.backtester.products):
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=self.backtester.total_pnl_histories[product],
                    mode='lines',
                    name=f'{product} PnL',
                    line=dict(color=color, width=2),
                    hovertemplate=f'{product} PnL: $%{{y:.2f}}<extra></extra>'
                ),
                row=2, col=1
            )

        # Per-product position plots
        for i, product in enumerate(self.backtester.products):
            color = colors[i % len(colors)]
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=self.backtester.position_histories[product],
                    mode='lines',
                    name=f'{product} Position',
                    line=dict(color=color, width=1.5),
                    hovertemplate=f'{product} Position: %{{y}}<extra></extra>'
                ),
                row=3, col=1
            )

        # Update layout
        fig.update_layout(
            title=dict(
                text=' Multi-Product Backtesting Dashboard',
                x=0.5,
                font=dict(size=20, color='white')
            ),
            template='plotly_dark',
            height=1000,
            showlegend=True,
            hovermode='x unified',
        )

        # Update axes
        fig.update_xaxes(title_text="Timestamp", row=3, col=1)
        fig.update_yaxes(title_text="Overall PnL ($)", row=1, col=1)
        fig.update_yaxes(title_text="Product PnL ($)", row=2, col=1)
        fig.update_yaxes(title_text="Position", row=3, col=1)

        # Render to HTML
        html_file = "multi_product_backtest_dashboard.html"
        pyo.plot(fig, filename=html_file, auto_open=True)
        self.log_message("✅ Multi-product interactive dashboard opened in browser!", 'success')

    def _create_single_product_plot(self):
        """Create single product interactive plot"""
        timestamps = self.backtester.timestamps
        positions = self.backtester.position_history
        realized_pnls = self.backtester.realized_pnl_history

        # Create interactive plot
        fig = make_subplots(
            rows=2, cols=1,
            vertical_spacing=0.12,
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}]]
        )

        # Position plot
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=positions,
                mode='lines',
                name='Position',
                line=dict(color='#00d4ff', width=2),
                hovertemplate='Timestamp: %{x}<br>Position: %{y}<extra></extra>'
            ),
            row=1, col=1
        )

        # Realized PnL plot
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=realized_pnls,
                mode='lines',
                name='Realized PnL',
                line=dict(color='#ffa500', width=2),
                hovertemplate='Timestamp: %{x}<br>Realized PnL: $%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            title=dict(
                text=' Single Product Backtesting Dashboard',
                x=0.5,
                font=dict(size=20, color='white')
            ),
            template='plotly_dark',
            height=750,
            showlegend=True,
            hovermode='x unified',
        )

        # Axes config
        fig.update_xaxes(
            title_text="Timestamp",
            rangeslider=dict(visible=True, thickness=0.05),
            row=2, col=1
        )
        fig.update_yaxes(title_text="Position", row=1, col=1)
        fig.update_yaxes(title_text="Profit & Loss ($)", row=2, col=1)

        # Render to HTML
        html_file = "single_product_backtest_dashboard.html"
        pyo.plot(fig, filename=html_file, auto_open=True)
        self.log_message("✅ Single product interactive dashboard opened in browser!", 'success')

    def show_summary(self):
        """Show performance summary in a new window"""
        if not self.backtester:
            messagebox.showerror("No Data", "Please run a backtest first")
            return

        # Create summary window
        summary_window = tk.Toplevel(self.root)
        summary_window.title(" Performance Summary")
        summary_window.geometry("900x800")
        summary_window.configure(bg=self.colors['bg_primary'])
        summary_window.resizable(True, True)

        # Make window modal
        summary_window.transient(self.root)
        summary_window.grab_set()

        # Create main frame with padding
        main_frame = tk.Frame(summary_window, bg=self.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        # Title frame
        title_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        title_frame.pack(fill='x', pady=(0, 20))

        title_label = tk.Label(title_frame,
                              text=" MULTI-PRODUCT BACKTESTING PERFORMANCE SUMMARY",
                              bg=self.colors['bg_primary'],
                              fg=self.colors['text_primary'],
                              font=('Arial', 14, 'bold'))
        title_label.pack()

        # Generate summary text
        if isinstance(self.backtester, MultiProductBacktester) and len(self.backtester.products) > 1:
            summary_text = self._generate_multi_product_summary()
        else:
            summary_text = self._generate_single_product_summary()

        # Create scrollable text frame
        text_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        text_frame.pack(fill='both', expand=True)

        # Create text widget with scrollbar
        text_widget = tk.Text(text_frame,
                             bg=self.colors['bg_secondary'],
                             fg=self.colors['text_primary'],
                             font=('Consolas', 9),
                             padx=20, pady=20,
                             wrap=tk.WORD,
                             relief='flat',
                             borderwidth=0,
                             insertbackground=self.colors['text_primary'],
                             selectbackground=self.colors['accent'])

        scrollbar = tk.Scrollbar(text_frame, bg=self.colors['bg_tertiary'],
                                troughcolor=self.colors['bg_secondary'])
        scrollbar.pack(side='right', fill='y')
        text_widget.pack(side='left', fill='both', expand=True)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        text_widget.insert('1.0', summary_text)
        text_widget.config(state='disabled')

        # Close button frame
        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(fill='x', pady=(15, 0))

        close_btn = tk.Button(button_frame,
                             text="✅ Close",
                             command=summary_window.destroy,
                             bg=self.colors['bg_tertiary'],
                             fg=self.colors['text_primary'],
                             font=('Arial', 10, 'bold'),
                             relief='flat',
                             padx=20, pady=8,
                             cursor='hand2')
        close_btn.pack(side='right')

        # Center the window
        summary_window.update_idletasks()
        x = (summary_window.winfo_screenwidth() // 2) - (summary_window.winfo_width() // 2)
        y = (summary_window.winfo_screenheight() // 2) - (summary_window.winfo_height() // 2)
        summary_window.geometry(f"+{x}+{y}")

    def _generate_multi_product_summary(self):
        """Generate summary for multi-product backtest"""
        overall_pnl = self.backtester.overall_pnl_history[-1] if self.backtester.overall_pnl_history else 0
        overall_realized = self.backtester.overall_realized_pnl_history[-1] if self.backtester.overall_realized_pnl_history else 0
        max_overall_pnl = max(self.backtester.overall_pnl_history) if self.backtester.overall_pnl_history else 0
        min_overall_pnl = min(self.backtester.overall_pnl_history) if self.backtester.overall_pnl_history else 0
        
        summary = f"""{'='*80}
 MULTI-PRODUCT BACKTESTING PERFORMANCE SUMMARY
{'='*80}

🌟 OVERALL PORTFOLIO PERFORMANCE:
• Total Products Traded: {len(self.backtester.products)}
• Overall Final PnL: ${overall_pnl:,.2f}
• Overall Realized PnL: ${overall_realized:,.2f}
• Maximum Overall PnL: ${max_overall_pnl:,.2f}
• Minimum Overall PnL: ${min_overall_pnl:,.2f}
• Overall Drawdown: ${max_overall_pnl - min_overall_pnl:,.2f}

📈 PER-PRODUCT BREAKDOWN:
"""
        
        for product in self.backtester.products:
            final_pos = self.backtester.positions[product]
            final_pnl = (self.backtester.total_pnl_histories[product][-1] 
                        if self.backtester.total_pnl_histories[product] else 0)
            final_realized = (self.backtester.realized_pnl_histories[product][-1] 
                            if self.backtester.realized_pnl_histories[product] else 0)
            max_pnl = (max(self.backtester.total_pnl_histories[product]) 
                      if self.backtester.total_pnl_histories[product] else 0)
            min_pnl = (min(self.backtester.total_pnl_histories[product]) 
                      if self.backtester.total_pnl_histories[product] else 0)
            
            summary += f"""
├── {product}:
│   ├── Final Position: {final_pos}
│   ├── Final PnL: ${final_pnl:,.2f}
│   ├── Realized PnL: ${final_realized:,.2f}
│   ├── Maximum PnL: ${max_pnl:,.2f}
│   ├── Minimum PnL: ${min_pnl:,.2f}
│   └── Product Drawdown: ${max_pnl - min_pnl:,.2f}
"""
        
        summary += f"""
 TRADING ACTIVITY:
• Total Timestamps: {len(self.backtester.timestamps):,}
• Strategy File: {self.algo_file.split('/')[-1] if self.algo_file else 'N/A'}
• Position Limit per Product: ±{self.backtester.POSITION_LIMIT}

🎯 PORTFOLIO SUMMARY:
{'✅ Profitable Portfolio' if overall_pnl > 0 else '❌ Loss-Making Portfolio'}
{'🎯 Diversified Trading' if len(self.backtester.products) > 1 else ' Single Product Focus'}

{'='*80}"""
        
        return summary

    def _generate_single_product_summary(self):
        """Generate summary for single product backtest"""
        final_pnl = self.backtester.pnl
        final_position = self.backtester.position
        max_pnl = max(self.backtester.realized_pnl_history) if self.backtester.realized_pnl_history else 0
        min_pnl = min(self.backtester.realized_pnl_history) if self.backtester.realized_pnl_history else 0
        
        # Calculate additional metrics
        positions = np.array(self.backtester.position_history)
        pnls = np.array(self.backtester.realized_pnl_history)
        max_position = np.max(np.abs(positions)) if len(positions) > 0 else 0
        pnl_volatility = np.std(pnls) if len(pnls) > 1 else 0
        max_drawdown = max_pnl - min_pnl if max_pnl > min_pnl else 0
        
        # Count position changes
        position_changes = 0
        if len(positions) > 1:
            for i in range(1, len(positions)):
                if positions[i] != positions[i-1]:
                    position_changes += 1

        summary = f"""{'='*80}
 SINGLE PRODUCT BACKTESTING PERFORMANCE SUMMARY
{'='*80}

 POSITION METRICS:
• Maximum Absolute Position: {max_position}
• Final Position: {final_position}
• Position Changes: {position_changes}
• Position Limit: ±{self.backtester.POSITION_LIMIT}

💰 PROFIT & LOSS METRICS:
• Final PnL: ${final_pnl:,.2f}
• Maximum PnL: ${max_pnl:,.2f}
• Minimum PnL: ${min_pnl:,.2f}
• Maximum Drawdown: ${max_drawdown:,.2f}
• PnL Volatility: ${pnl_volatility:,.2f}

📈 TRADING ACTIVITY:
• Total Timestamps: {len(self.backtester.timestamps):,}
• Data Points: {len(positions):,}
• Strategy File: {self.algo_file.split('/')[-1] if self.algo_file else 'N/A'}

 PERFORMANCE RATIOS:
• Return/Risk Ratio: {(abs(final_pnl) / pnl_volatility):,.2f} (if vol > 0)
• Profit Factor: {(max_pnl / abs(min_pnl)):,.2f} (if min_pnl < 0)

🎯 SUMMARY:
{'✅ Profitable Strategy' if final_pnl > 0 else '❌ Loss-Making Strategy'}
{'🎯 Low Risk' if pnl_volatility < abs(final_pnl) else '⚠️ High Volatility'}

{'='*80}"""
        
        return summary


def main():
    root = tk.Tk()
    app = ModernMultiProductBacktesterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()