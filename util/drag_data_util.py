from typing import Optional
import tkinter as tk

class DragData:
    def __init__(self):
        self.card = None  # Cardオブジェクトへの参照
        self.origin: Optional[str] = None
        self.widget: Optional[tk.Widget] = None
        self.start_x: int = 0
        self.start_y: int = 0
