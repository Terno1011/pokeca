# utils/special_condition_helper.py
# Version: 1.0
# Updated: 2025-06-14 12:00
# 特殊状態によるにげる制限チェック用ヘルパー

from typing import Tuple
from models.card import Card

class SpecialConditionHelper:
    """特殊状態に関連する処理を行うヘルパークラス"""
    
    @staticmethod
    def can_retreat(pokemon: Card) -> Tuple[bool, str]:
        """
        ポケモンがにげることができるかをチェック
        
        Args:
            pokemon: チェック対象のポケモンカード
            
        Returns:
            Tuple[bool, str]: (にげる可否, 制限理由)
        """
        try:
            # ポケモンに特殊状態があるかチェック
            special_conditions = getattr(pokemon, 'special_conditions', [])
            
            # ねむり状態
            if 'sleep' in special_conditions:
                return False, "ねむり状態のためにげることができません"
            
            # マヒ状態
            if 'paralyzed' in special_conditions:
                return False, "マヒ状態のためにげることができません"
            
            # 混乱状態は通常にげることに影響しない
            # if 'confused' in special_conditions:
            #     return True, ""  # 混乱状態でもにげることは可能
            
            # どく状態ややけど状態もにげることに影響しない
            # if 'poisoned' in special_conditions:
            #     return True, ""  # どく状態でもにげることは可能
            # if 'burned' in special_conditions:
            #     return True, ""  # やけど状態でもにげることは可能
            
            # その他の特別な効果による制限（将来実装）
            # 例: 「にげることができない」効果を持つワザやポケモンの特性
            
            return True, ""
        
        except Exception as e:
            print(f"特殊状態チェックエラー: {e}")
            # エラーが発生した場合は安全側に倒してにげることを許可
            return True, ""
    
    @staticmethod
    def apply_special_condition(pokemon: Card, condition: str) -> bool:
        """
        ポケモンに特殊状態を適用
        
        Args:
            pokemon: 対象ポケモン
            condition: 特殊状態名 (sleep, paralyzed, confused, poisoned, burned)
            
        Returns:
            bool: 適用成功可否
        """
        try:
            if not hasattr(pokemon, 'special_conditions'):
                pokemon.special_conditions = []
            
            if condition not in pokemon.special_conditions:
                pokemon.special_conditions.append(condition)
                print(f"{pokemon.name}に{condition}状態を付与")
                return True
            
            return False
        
        except Exception as e:
            print(f"特殊状態適用エラー: {e}")
            return False
    
    @staticmethod
    def remove_special_condition(pokemon: Card, condition: str) -> bool:
        """
        ポケモンから特殊状態を除去
        
        Args:
            pokemon: 対象ポケモン
            condition: 除去する特殊状態名
            
        Returns:
            bool: 除去成功可否
        """
        try:
            if hasattr(pokemon, 'special_conditions') and condition in pokemon.special_conditions:
                pokemon.special_conditions.remove(condition)
                print(f"{pokemon.name}から{condition}状態を除去")
                return True
            
            return False
        
        except Exception as e:
            print(f"特殊状態除去エラー: {e}")
            return False
    
    @staticmethod
    def clear_all_special_conditions(pokemon: Card) -> bool:
        """
        ポケモンからすべての特殊状態を除去
        
        Args:
            pokemon: 対象ポケモン
            
        Returns:
            bool: 除去成功可否
        """
        try:
            if hasattr(pokemon, 'special_conditions'):
                conditions_cleared = len(pokemon.special_conditions)
                pokemon.special_conditions = []
                print(f"{pokemon.name}からすべての特殊状態を除去（{conditions_cleared}個）")
                return True
            
            return False
        
        except Exception as e:
            print(f"特殊状態全除去エラー: {e}")
            return False
    
    @staticmethod
    def get_special_conditions_display(pokemon: Card) -> str:
        """
        ポケモンの特殊状態の表示用文字列を取得
        
        Args:
            pokemon: 対象ポケモン
            
        Returns:
            str: 特殊状態の表示文字列
        """
        try:
            if not hasattr(pokemon, 'special_conditions') or not pokemon.special_conditions:
                return ""
            
            condition_map = {
                'sleep': '😴ねむり',
                'paralyzed': '⚡マヒ',
                'confused': '😵混乱',
                'poisoned': '💜どく',
                'burned': '🔥やけど'
            }
            
            display_conditions = []
            for condition in pokemon.special_conditions:
                display_conditions.append(condition_map.get(condition, condition))
            
            return " ".join(display_conditions)
        
        except Exception as e:
            print(f"特殊状態表示取得エラー: {e}")
            return ""