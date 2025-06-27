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

from src.backtester import Backtester

class ModernBacktesterGUI:
    def __init__(self, root):
        self.root = root
        root.title("SOC Backtester")
        root.geometry("1200x800")
        
        # Configure dark theme
        self.setup_dark_theme()
        
        self.price_file = ""
        self.trades_file = ""
        self.algo_file = ""
        self.backtester = None
        
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
        
        title_label = ttk.Label(header_frame, text="🚀 SoC Backtester", 
                               style='Header.TLabel')
        title_label.pack()
        
        # File loading section
        files_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        files_frame.pack(fill='x', pady=(0, 20))
        
        files_label = ttk.Label(files_frame, text="📁 Data Files", style='Header.TLabel')
        files_label.pack(anchor='w')
        
        # File buttons frame
        buttons_frame = ttk.Frame(files_frame, style='Dark.TFrame')
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        # File loading buttons
        self.price_btn = ttk.Button(buttons_frame, text="📊 Load Price Data", 
                                   command=self.load_price, style='Dark.TButton')
        self.price_btn.pack(side='left', padx=(0, 10))
        
        self.trades_btn = ttk.Button(buttons_frame, text="💱 Load Trades Data", 
                                    command=self.load_trades, style='Dark.TButton')
        self.trades_btn.pack(side='left', padx=(0, 10))
        
        self.algo_btn = ttk.Button(buttons_frame, text="🧠 Load Strategy", 
                                  command=self.load_algo, style='Dark.TButton')
        self.algo_btn.pack(side='left', padx=(0, 10))
        
        # Run button
        self.run_btn = ttk.Button(buttons_frame, text="🚀 Run Backtest", 
                                 command=self.run_backtest_threaded, style='Dark.TButton')
        self.run_btn.pack(side='left', padx=(20, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(buttons_frame, style='Dark.Horizontal.TProgressbar', 
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
        
        self.interactive_btn = ttk.Button(viz_buttons_frame, text="📊 Open Interactive Dashboard", 
                                         command=self.open_interactive_plot, style='Dark.TButton',
                                         state='disabled')
        self.interactive_btn.pack(side='left', padx=(0, 10))
        
        self.summary_btn = ttk.Button(viz_buttons_frame, text="📋 Performance Summary", 
                                     command=self.show_summary, style='Dark.TButton',
                                     state='disabled')
        self.summary_btn.pack(side='left', padx=(0, 10))
        
        self.export_btn = ttk.Button(viz_buttons_frame, text="💾 Export Results", 
                                    command=self.export_results, style='Dark.TButton',
                                    state='disabled')
        self.export_btn.pack(side='left')
        
        # Quick stats frame
        self.stats_frame = ttk.Frame(results_frame, style='Dark.TFrame')
        self.stats_frame.pack(fill='x', pady=(10, 0))
        
        self.quick_stats_label = ttk.Label(self.stats_frame, text="📊 Run a backtest to see results", 
                                          style='Dark.TLabel')
        self.quick_stats_label.pack(anchor='w')
        
        # File status labels
        self.create_status_labels(files_frame)
        
        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Initial log message
        self.log_message("🌟 Welcome to Advanced Backtester Pro!")
        self.log_message("💡 Load your data files and strategy to get started.")
        self.log_message("⌨️  Keyboard shortcuts: Ctrl+O (Open files), Ctrl+R (Run), Ctrl+S (Summary)")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        self.root.bind('<Control-r>', lambda e: self.run_backtest_threaded())
        self.root.bind('<Control-s>', lambda e: self.show_summary() if self.backtester else None)
        self.root.bind('<Control-d>', lambda e: self.open_interactive_plot() if self.backtester else None)
        self.root.bind('<F5>', lambda e: self.run_backtest_threaded())
        self.root.bind('<Escape>', lambda e: self.root.quit())
    
    def create_status_labels(self, parent):
        """Create file status indicators"""
        status_frame = ttk.Frame(parent, style='Dark.TFrame')
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.price_status = ttk.Label(status_frame, text="❌ Price data: Not loaded", 
                                     style='Dark.TLabel')
        self.price_status.pack(anchor='w')
        
        self.trades_status = ttk.Label(status_frame, text="❌ Trades data: Not loaded", 
                                      style='Dark.TLabel')
        self.trades_status.pack(anchor='w')
        
        self.algo_status = ttk.Label(status_frame, text="❌ Strategy: Not loaded", 
                                    style='Dark.TLabel')
        self.algo_status.pack(anchor='w')
    
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
    
    def load_price(self):
        self.price_file = filedialog.askopenfilename(
            title="Select Price Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if self.price_file:
            self.log_message(f"Price data loaded: {self.price_file.split('/')[-1]}", 'success')
            self.price_status.config(text=f"✅ Price data: {self.price_file.split('/')[-1]}")
        
    def load_trades(self):
        self.trades_file = filedialog.askopenfilename(
            title="Select Trades Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if self.trades_file:
            self.log_message(f"Trades data loaded: {self.trades_file.split('/')[-1]}", 'success')
            self.trades_status.config(text=f"✅ Trades data: {self.trades_file.split('/')[-1]}")
    
    def load_algo(self):
        self.algo_file = filedialog.askopenfilename(
            title="Select Strategy Python File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if self.algo_file:
            self.log_message(f"Strategy loaded: {self.algo_file.split('/')[-1]}", 'success')
            self.algo_status.config(text=f"✅ Strategy: {self.algo_file.split('/')[-1]}")
    
    def run_backtest_threaded(self):
        """Run backtest in separate thread to prevent GUI freezing"""
        if not self.price_file or not self.trades_file or not self.algo_file:
            messagebox.showerror("Missing Files", "Please load all required files first")
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
            
            # Initialize backtester
            self.backtester = Backtester(self.price_file, self.trades_file, trader)
            self.log_message("📊 Running backtest simulation...")
            
            # Run backtest
            self.backtester.run()
            
            # Log results
            self.log_message("🎉 Backtest completed successfully!", 'success')
            self.log_message(f"📊 Final Position: {self.backtester.position}")
            # self.log_message(f"💰 Final PnL: {self.backtester.pnl:.2f}")
            
            # Enable visualization buttons
            self.interactive_btn.config(state='normal')
            self.summary_btn.config(state='normal')
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
        
        pro = self.backtester.realized_pnl_history
        final_pnl = pro[-1]
        final_position = self.backtester.position
        max_pnl = max(self.backtester.realized_pnl_history) if self.backtester.realized_pnl_history else 0
        min_pnl = min(self.backtester.realized_pnl_history) if self.backtester.realized_pnl_history else 0
        
        stats_text = f"💰 Final PnL: ${final_pnl:,.2f} | 📊 Position: {final_position} | 📈 Max PnL: ${max_pnl:,.2f} | 📉 Min PnL: ${min_pnl:,.2f}"
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
            
            # Create DataFrame with results
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
    
            # Prepare data
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
                    line=dict(color='#00d4ff', width=0.5),
                    hovertemplate='<b>Timestamp:</b> %{x}<br>' +
                                  '<b>Position:</b> %{y}<extra></extra>'
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
                    hovertemplate='<b>Timestamp:</b> %{x}<br>' +
                                  '<b>Realized PnL:</b> $%{y:.2f}<extra></extra>'
                ),
                row=2, col=1
            )
    
            # Update layout
            fig.update_layout(
                title=dict(
                    text='📊 Interactive Backtesting Dashboard',
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
    
            # Manual subplot titles
            fig.update_layout(
                annotations=[
                    dict(
                        text="Position Over Time",
                        x=0.5, y=1.07,
                        xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=16, color="white")
                    ),
                    dict(
                        text="Profit & Loss Over Time",
                        x=0.5, y=0.45,
                        xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=16, color="white")
                    )
                ]
            )
    
            # Render to HTML
            html_file = "backtest_dashboard.html"
            pyo.plot(fig, filename=html_file, auto_open=True)
    
            self.log_message("✅ Interactive dashboard opened in browser!", 'success')
    
        except Exception as e:
            self.log_message(f"❌ Error creating dashboard: {str(e)}", 'error')
    
    def show_summary(self):
        """Show performance summary in a new window"""
        if not self.backtester:
            messagebox.showerror("No Data", "Please run a backtest first")
            return
        
        # Create summary window
        summary_window = tk.Toplevel(self.root)
        summary_window.title("📊 Performance Summary")
        summary_window.geometry("700x600")
        summary_window.configure(bg=self.colors['bg_primary'])
        summary_window.resizable(True, True)
        
        # Make window modal
        summary_window.transient(self.root)
        summary_window.grab_set()
        
        # Calculate metrics
        positions = np.array(self.backtester.position_history)
        # pnls = np.array(self.backtester.pnl_history)
        pnls = np.array(self.backtester.realized_pnl_history)
        
        max_position = np.max(np.abs(positions)) if len(positions) > 0 else 0
        max_pnl = np.max(pnls) if len(pnls) > 0 else 0
        min_pnl = np.min(pnls) if len(pnls) > 0 else 0
        final_pnl = pnls[-1] if len(pnls) > 0 else 0
        
        # Calculate additional metrics
        pnl_volatility = np.std(pnls) if len(pnls) > 1 else 0
        total_return = final_pnl
        max_drawdown = max_pnl - min_pnl if max_pnl > min_pnl else 0
        
        # Count position changes
        position_changes = 0
        if len(positions) > 1:
            for i in range(1, len(positions)):
                if positions[i] != positions[i-1]:
                    position_changes += 1
        
        # Create main frame with padding
        main_frame = tk.Frame(summary_window, bg=self.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Title frame
        title_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        title_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(title_frame, 
                              text="📊 BACKTESTING PERFORMANCE SUMMARY",
                              bg=self.colors['bg_primary'],
                              fg=self.colors['text_primary'],
                              font=('Arial', 14, 'bold'))
        title_label.pack()
        
        # Create summary text with better formatting
        summary_text = f"""{'='*60}

📊 POSITION METRICS:
   • Maximum Absolute Position: {max_position}
   • Final Position: {self.backtester.position}
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

🔍 DATA SOURCES:
   • Price Data: {self.price_file.split('/')[-1] if self.price_file else 'N/A'}
   • Trades Data: {self.trades_file.split('/')[-1] if self.trades_file else 'N/A'}

📊 PERFORMANCE RATIOS:
   • Return/Risk Ratio: {(abs(final_pnl) / pnl_volatility):,.2f} (if vol > 0)
   • Profit Factor: {(max_pnl / abs(min_pnl) if abs(min_pnl) else 1e-4):,.2f} (if min_pnl < 0)

🎯 SUMMARY:
   {'✅ Profitable Strategy' if final_pnl > 0 else '❌ Loss-Making Strategy'}
   {'🎯 Low Risk' if pnl_volatility < abs(final_pnl) else '⚠️ High Volatility'}

{'='*60}"""
        
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


def main():
    root = tk.Tk()
    app = ModernBacktesterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()