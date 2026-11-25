import tkinter as tk
from gui import CPUSchedulerApp


if __name__ == "__main__":
    root = tk.Tk()
    app = CPUSchedulerApp(root)
    root.mainloop()