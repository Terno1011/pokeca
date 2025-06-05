# utils/drag_data.py
# Version: 1.0
# Updated: 2024-12-06

from typing import Optional
import tkinter as tk

class DragData:
    """ドラッグ&ドロップ操作のデータを管理するクラス"""
    
    def __init__(self):
        self.card = None  # Cardオブジェクトへの参照
        self.origin: Optional[str] = None  # ドラッグ元の場所
        self.widget: Optional[tk.Widget] = None  # ドラッグされているウィジェット
        self.start_x: int = 0  # ドラッグ開始時のX座標
        self.start_y: int = 0  # ドラッグ開始時のY座標
    
    def reset(self):
        """ドラッグデータをリセット"""
        self.card = None
        self.origin = None
        self.widget = None
        self.start_x = 0
        self.start_y = 0
    
    def is_dragging(self) -> bool:
        """現在ドラッグ中かどうか"""
        return self.card is not None
    
    def set_drag_data(self, card, origin: str, widget: tk.Widget, x: int, y: int):
        """ドラッグデータを設定"""
        self.card = card
        self.origin = origin
        self.widget = widget
        self.start_x = x
        self.start_y = y