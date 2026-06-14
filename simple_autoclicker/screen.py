import sys


def get_virtual_screen_bounds() -> tuple[int, int, int, int]:
    """Return (min_x, min_y, max_x, max_y) for the virtual desktop across monitors."""
    if sys.platform == "win32":
        import ctypes

        user32 = ctypes.windll.user32
        min_x = user32.GetSystemMetrics(76)
        min_y = user32.GetSystemMetrics(77)
        width = user32.GetSystemMetrics(78)
        height = user32.GetSystemMetrics(79)
        return min_x, min_y, min_x + width - 1, min_y + height - 1

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        return 0, 0, width - 1, height - 1
    except Exception:
        return 0, 0, 1919, 1079
