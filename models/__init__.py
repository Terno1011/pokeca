# models/__init__.py
# Version: 4.23
# Updated: 2025-06-12 11:45
# 不要ファイル削除・簡略化版

from .card import Card, CardType, TrainerType, SpecialCondition
from .game_state import GameState

__all__ = [
    'Card', 
    'CardType', 
    'TrainerType', 
    'SpecialCondition', 
    'GameState'
]

# バージョン情報
__version__ = "4.23"
__status__ = "不要ファイル削除・簡略化版"