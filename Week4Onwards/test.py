import tkinter as tk
from tkinter import ttk

root = tk.Tk()
style = ttk.Style()
style.theme_use('clam')  # clam is stable

# Clone layout to prevent segfault
style.layout('Dark.TButton', style.layout('TButton'))

style.configure('Dark.TButton',
                foreground='white', background='#222',
                padding=6, relief='flat')

style.map('Dark.TButton',
          background=[('active', '#444')],
          foreground=[('disabled', '#888')])

frame = ttk.Frame(root)
frame.pack(padx=10, pady=10)

ttk.Button(frame, text="One", style="Dark.TButton").pack(side="left", padx=5)
ttk.Button(frame, text="Two", style="Dark.TButton").pack(side="left", padx=5)
ttk.Button(frame, text="Three", style="Dark.TButton").pack(side="left", padx=5)

root.mainloop()
