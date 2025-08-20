# models/card.py
# Version: 4.5
# Updated: 2024-12-06
# カードモデル：簡素化版

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum
import random

class CardType(Enum):
    POKEMON = "POKEMON"
    TRAINER = "TRAINER"
    ENERGY = "ENERGY"
    TOOL = "TOOL"  # ポケモンのどうぐ

class TrainerType(Enum):
    ITEM = "item"        # グッズ
    SUPPORTER = "supporter"
    STADIUM = "stadium"
    POKEMON_TOOL = "pokemon_tool"

class SpecialCondition(Enum):
    """特殊状態の種類"""
    POISON = "どく"
    BURN = "やけど"
    SLEEP = "ねむり"
    PARALYSIS = "マヒ"
    CONFUSION = "こんらん"

@dataclass
class Card:
    id: int
    name: str
    card_type: CardType
    hp: Optional[int] = None
    
    # タイプ情報
    pokemon_type: Optional[str] = None      # ポケモンのタイプ
    energy_kind: Optional[str] = None       # エネルギーの種類
    
    # 特性
    ability_name: Optional[str] = None
    ability_description: Optional[str] = None
    
    # ワザ1
    attack_name: Optional[str] = None
    attack_power: Optional[int] = None
    attack_cost_types: Optional[Dict[str, int]] = None
    attack_cost: Optional[int] = None
    attack_effect: Optional[str] = None
    
    # ワザ2
    attack2_name: Optional[str] = None
    attack2_power: Optional[int] = None
    attack2_cost_types: Optional[Dict[str, int]] = None
    attack2_cost: Optional[int] = None
    attack2_effect: Optional[str] = None
    
    # バトル関連
    weakness: Optional[str] = None
    resistance: Optional[str] = None
    retreat_cost: Optional[int] = None
    
    # 進化システム
    evolve_step: int = 0                    # 進化段階（0=基本）
    evolves_from: Optional[str] = None      # 進化元
    
    # 特殊ルール・分類
    rule: Optional[str] = None
    class_type: Optional[str] = None
    
    # トレーナーカード関連
    trainer_type: Optional[TrainerType] = None
    trainers_description: Optional[str] = None
    
    # メタデータ
    rarity: Optional[str] = None
    regulation: Optional[str] = None
    
    # ゲーム中の状態
    damage_taken: int = 0
    attached_energy: List['Card'] = field(default_factory=list)
    attached_tools: List['Card'] = field(default_factory=list)
    special_conditions: Set[SpecialCondition] = field(default_factory=set)
    summoned_this_turn: bool = False
    evolved_this_turn: bool = False
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.attack_cost_types is None:
            self.attack_cost_types = {}
        if self.attack2_cost_types is None:
            self.attack2_cost_types = {}
    
    def can_evolve_from(self, base_pokemon: 'Card') -> bool:
        """このカードが指定のポケモンから進化できるかチェック"""
        return (self.card_type == CardType.POKEMON and 
                base_pokemon.card_type == CardType.POKEMON and
                self.evolves_from == base_pokemon.name)
    
    def get_pokemon_type(self) -> Optional[str]:
        """ポケモンのタイプを取得"""
        if self.card_type == CardType.POKEMON:
            return self.pokemon_type
        elif self.card_type == CardType.ENERGY:
            return self.energy_kind
        return None
    
    def can_attach_tool(self) -> bool:
        """ポケモンのどうぐを装備できるかチェック"""
        return (self.card_type == CardType.POKEMON and 
                len(self.attached_tools) == 0)
    
    def add_special_condition(self, condition: SpecialCondition):
        """特殊状態を追加"""
        # 相互排他的な特殊状態の処理
        exclusive_conditions = {SpecialCondition.SLEEP, SpecialCondition.PARALYSIS, SpecialCondition.CONFUSION}
        
        if condition in exclusive_conditions:
            # 既存の排他的状態を削除
            self.special_conditions = {c for c in self.special_conditions if c not in exclusive_conditions}
        
        self.special_conditions.add(condition)
    
    def remove_special_condition(self, condition: SpecialCondition):
        """特殊状態を削除"""
        self.special_conditions.discard(condition)
    
    def has_special_condition(self, condition: SpecialCondition) -> bool:
        """特殊状態を持っているかチェック"""
        return condition in self.special_conditions
    
    def clear_special_conditions(self):
        """全ての特殊状態をクリア"""
        self.special_conditions.clear()
    
    def is_knocked_out(self) -> bool:
        """きぜつしているかチェック"""
        if self.card_type != CardType.POKEMON or not self.hp:
            return False
        return self.damage_taken >= self.hp
    
    def heal_damage(self, amount: int):
        """ダメージを回復"""
        self.damage_taken = max(0, self.damage_taken - amount)
    
    def deal_damage(self, amount: int):
        """ダメージを与える"""
        self.damage_taken += amount
    
    @property
    def current_hp(self) -> int:
        """現在のHPを取得"""
        if not self.hp:
            return 0
        return max(0, self.hp - self.damage_taken)