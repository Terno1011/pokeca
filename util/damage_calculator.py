# utils/damage_calculator.py
# Version: 2.1
# Updated: 2025-06-11 16:45
# HP引き継ぎバグ修正対応ダメージ計算システム

import copy
from typing import Tuple, List, Optional
from models.card import Card
from models.game_state import GameState

class DamageCalculator:
    """ダメージ計算と適用を行うクラス（HP引き継ぎバグ修正版）"""
    
    @staticmethod
    def calculate_damage(attacker: Card, defender: Card, attack_number: int) -> Tuple[int, List[str]]:
        """
        ダメージを計算（旧形式カードデータ対応版）
        
        Args:
            attacker: 攻撃するポケモン
            defender: 攻撃を受けるポケモン
            attack_number: ワザ番号（1 or 2）
            
        Returns:
            Tuple[int, List[str]]: (最終ダメージ, 計算詳細メッセージ)
        """
        messages = []
        
        try:
            print(f"🔍 ダメージ計算開始: {attacker.name} → {defender.name}, ワザ{attack_number}")
            
            # HP引き継ぎバグ修正確認：カードインスタンスの独立性確認
            if hasattr(defender, '_instance_id'):
                messages.append(f"対象: {defender.name} (インスタンス: {defender._instance_id})")
            
            # 基本ダメージの取得（旧形式対応）
            if attack_number == 1:
                base_damage = getattr(attacker, 'attack_power', 0) or 0
                attack_name = getattr(attacker, 'attack_name', f'ワザ{attack_number}')
                attack_effect = getattr(attacker, 'attack_effect', '')
            elif attack_number == 2:
                base_damage = getattr(attacker, 'attack2_power', 0) or 0
                attack_name = getattr(attacker, 'attack2_name', f'ワザ{attack_number}')
                attack_effect = getattr(attacker, 'attack2_effect', '')
            else:
                print("❌ 無効なワザ番号です")
                return 0, ["無効なワザ番号です"]
            
            print(f"  - ワザ名: {attack_name}")
            print(f"  - 基本ダメージ: {base_damage}")
            
            if base_damage == 0:
                messages.append(f"「{attack_name}」の基本ダメージ: 0")
                return 0, messages
            
            messages.append(f"「{attack_name}」の基本ダメージ: {base_damage}")
            
            final_damage = base_damage
            
            # 弱点計算
            weakness_multiplier = DamageCalculator._calculate_weakness(attacker, defender, messages)
            final_damage = int(final_damage * weakness_multiplier)
            print(f"  - 弱点計算後: {final_damage}")
            
            # 抵抗力計算
            resistance_reduction = DamageCalculator._calculate_resistance(attacker, defender, messages)
            final_damage = max(0, final_damage - resistance_reduction)
            print(f"  - 抵抗力計算後: {final_damage}")
            
            # エネルギー効率によるボーナス計算
            energy_bonus = DamageCalculator._calculate_energy_efficiency_bonus(
                attacker, attack_number, final_damage, messages
            )
            final_damage += energy_bonus
            
            # 最終ダメージ
            if final_damage != base_damage:
                messages.append(f"最終ダメージ: {final_damage}")
            
            print(f"✅ ダメージ計算完了: {final_damage}")
            return final_damage, messages
            
        except Exception as e:
            print(f"❌ ダメージ計算エラー: {e}")
            return 0, [f"ダメージ計算エラー: {e}"]
    
    @staticmethod
    def _calculate_energy_efficiency_bonus(attacker: Card, attack_number: int, 
                                         current_damage: int, messages: List[str]) -> int:
        """
        エネルギー効率によるボーナス計算
        
        一部の特殊なワザで、余分なエネルギーがある場合のダメージボーナスを計算
        """
        try:
            # エネルギー依存ダメージの判定
            if attack_number == 1:
                attack_effect = getattr(attacker, 'attack_effect', '')
                cost_types = attacker.attack_cost_types or {}
            else:
                attack_effect = getattr(attacker, 'attack2_effect', '')
                cost_types = getattr(attacker, 'attack2_cost_types', {}) or {}
            
            # 現在はボーナスなし（将来実装用の基盤）
            return 0
            
        except Exception as e:
            messages.append(f"エネルギー効率計算エラー: {e}")
            return 0
    
    @staticmethod
    def _calculate_weakness(attacker: Card, defender: Card, messages: List[str]) -> float:
        """弱点による倍率を計算"""
        try:
            if not defender.weakness:
                return 1.0
            
            # 攻撃側のタイプを取得
            attacker_type = getattr(attacker, 'pokemon_type', None)
            if not attacker_type:
                return 1.0
            
            # タイプ名の正規化
            attacker_type = DamageCalculator._normalize_type_name(attacker_type)
            weakness_type = DamageCalculator._normalize_type_name(defender.weakness)
            
            if attacker_type == weakness_type:
                messages.append(f"弱点({weakness_type})により2倍ダメージ！")
                return 2.0
            
            return 1.0
            
        except Exception as e:
            messages.append(f"弱点計算エラー: {e}")
            return 1.0
    
    @staticmethod
    def _calculate_resistance(attacker: Card, defender: Card, messages: List[str]) -> int:
        """抵抗力による軽減ダメージを計算"""
        try:
            if not defender.resistance:
                return 0
            
            # 攻撃側のタイプを取得
            attacker_type = getattr(attacker, 'pokemon_type', None)
            if not attacker_type:
                return 0
            
            # タイプ名の正規化
            attacker_type = DamageCalculator._normalize_type_name(attacker_type)
            resistance_type = DamageCalculator._normalize_type_name(defender.resistance)
            
            if attacker_type == resistance_type:
                messages.append(f"抵抗力({resistance_type})により-30ダメージ")
                return 30
            
            return 0
            
        except Exception as e:
            messages.append(f"抵抗力計算エラー: {e}")
            return 0
    
    @staticmethod
    def _normalize_type_name(type_name: str) -> str:
        """タイプ名の正規化"""
        type_mapping = {
            '草': '草', 'くさ': '草', 'Grass': '草',
            '炎': '炎', 'ほのお': '炎', 'Fire': '炎',
            '水': '水', 'みず': '水', 'Water': '水',
            '雷': '雷', 'でんき': '雷', 'かみなり': '雷', 'Electric': '雷',
            '超': '超', 'エスパー': '超', 'Psychic': '超',
            '闘': '闘', 'かくとう': '闘', 'Fighting': '闘',
            '悪': '悪', 'あく': '悪', 'Dark': '悪',
            '鋼': '鋼', 'はがね': '鋼', 'Metal': '鋼',
            # 無色タイプの正規化
            '無色': '無色', 'ノーマル': '無色', 'Colorless': '無色'
        }
        
        return type_mapping.get(type_name, type_name)
    
    @staticmethod
    def apply_damage(defender: Card, damage: int) -> Tuple[bool, List[str]]:
        """ダメージを適用（HP引き継ぎバグ修正版）"""
        messages = []
        
        try:
            if damage <= 0:
                messages.append("ダメージは与えられませんでした")
                return False, messages
            
            # HP引き継ぎバグ修正確認：ダメージ適用前の状態確認
            old_damage = getattr(defender, 'damage_taken', 0)
            instance_info = getattr(defender, '_instance_id', 'unknown')
            
            # ダメージカウンターの更新
            defender.damage_taken = old_damage + damage
            
            messages.append(f"{defender.name}に{damage}ダメージ！")
            
            if hasattr(defender, '_instance_id'):
                messages.append(f"(インスタンス: {instance_info}, 累積ダメージ: {defender.damage_taken})")
            
            # HP状況の確認
            if defender.hp:
                current_hp = defender.hp - defender.damage_taken
                messages.append(f"{defender.name}の残りHP: {max(0, current_hp)}/{defender.hp}")
                
                # きぜつ判定
                if defender.damage_taken >= defender.hp:
                    messages.append(f"{defender.name}はきぜつしました！")
                    return True, messages
            
            return False, messages
            
        except Exception as e:
            messages.append(f"ダメージ適用エラー: {e}")
            return False, messages
    
    @staticmethod
    def handle_pokemon_knockout(game_state: GameState, knocked_out_pokemon: Card, 
                              owner: str, messages: List[str]):
        """
        ポケモンがきぜつした場合の処理（HP引き継ぎバグ修正版）
        
        重要：交代時にポケモンの状態が正しくリセットされることを確認
        """
        try:
            if owner == "player":
                if game_state.player_active == knocked_out_pokemon:
                    # HP引き継ぎバグ修正確認：きぜつしたポケモンの情報出力
                    instance_info = getattr(knocked_out_pokemon, '_instance_id', 'unknown')
                    messages.append(f"きぜつしたポケモン: {knocked_out_pokemon.name} (インスタンス: {instance_info})")
                    
                    game_state.player_active = None
                    messages.append("あなたのバトル場が空になりました")
                    
                    # ベンチにポケモンがいれば交代が必要
                    bench_pokemon = [p for p in game_state.player_bench if p is not None]
                    if bench_pokemon:
                        messages.append("ベンチからポケモンをバトル場に出してください")
                        # HP引き継ぎバグ修正確認：ベンチポケモンの状態確認
                        for i, pokemon in enumerate(bench_pokemon):
                            if pokemon:
                                bench_instance = getattr(pokemon, '_instance_id', 'unknown')
                                messages.append(f"ベンチ{i+1}: {pokemon.name} (HP: {pokemon.current_hp}/{pokemon.hp}, インスタンス: {bench_instance})")
                    else:
                        messages.append("ベンチにポケモンがいません！ゲーム終了です！")
                        
            else:  # opponent
                if game_state.opponent_active == knocked_out_pokemon:
                    # HP引き継ぎバグ修正確認：きぜつしたポケモンの情報出力
                    instance_info = getattr(knocked_out_pokemon, '_instance_id', 'unknown')
                    messages.append(f"相手のきぜつしたポケモン: {knocked_out_pokemon.name} (インスタンス: {instance_info})")
                    
                    game_state.opponent_active = None
                    messages.append("相手のバトル場が空になりました")
                    
                    # ベンチにポケモンがいれば自動で交代
                    bench_pokemon = [p for p in game_state.opponent_bench if p is not None]
                    if bench_pokemon:
                        # 最初のベンチポケモンをバトル場に（HP引き継ぎバグ修正版）
                        for i, pokemon in enumerate(game_state.opponent_bench):
                            if pokemon is not None:
                                # 重要：ポケモン交代時の状態確認
                                replacement_instance = getattr(pokemon, '_instance_id', 'unknown')
                                original_damage = pokemon.damage_taken
                                
                                # バトル場に移動
                                game_state.opponent_active = pokemon
                                game_state.opponent_bench[i] = None
                                
                                # HP引き継ぎバグ修正確認：交代後のダメージ状態確認
                                messages.append(f"相手が{pokemon.name}をバトル場に出しました")
                                messages.append(f"(交代ポケモン - インスタンス: {replacement_instance}, ダメージ: {original_damage})")
                                
                                if original_damage > 0:
                                    messages.append("⚠️ 注意: 交代したポケモンに既存ダメージがあります（HP引き継ぎバグの可能性）")
                                
                                break
                    else:
                        messages.append("相手のベンチにポケモンがいません！あなたの勝利です！")
        
        except Exception as e:
            messages.append(f"バトル場交代処理エラー: {e}")
    
    @staticmethod
    def _apply_attack_effects(attacker: Card, defender: Card, attack_number: int) -> List[str]:
        """攻撃効果を適用（HP引き継ぎバグ修正版）"""
        messages = []
        
        try:
            # 攻撃効果の取得
            if attack_number == 1:
                effect_text = getattr(attacker, 'attack_effect', None)
            else:
                effect_text = getattr(attacker, 'attack2_effect', None)
            
            if not effect_text:
                return messages
            
            # 基本的な特殊状態付与のみ実装
            from models.card import SpecialCondition
            
            if "こんらん" in effect_text or "混乱" in effect_text:
                defender.add_special_condition(SpecialCondition.CONFUSION)
                messages.append(f"{defender.name}がこんらんしました！")
            
            if "どく" in effect_text or "毒" in effect_text:
                defender.add_special_condition(SpecialCondition.POISON)
                messages.append(f"{defender.name}がどくになりました！")
            
            if "やけど" in effect_text or "火傷" in effect_text:
                defender.add_special_condition(SpecialCondition.BURN)
                messages.append(f"{defender.name}がやけどしました！")
            
            if "マヒ" in effect_text or "麻痺" in effect_text:
                defender.add_special_condition(SpecialCondition.PARALYSIS)
                messages.append(f"{defender.name}がマヒしました！")
            
            if "ねむり" in effect_text or "眠り" in effect_text:
                defender.add_special_condition(SpecialCondition.SLEEP)
                messages.append(f"{defender.name}がねむりました！")
            
            # HP引き継ぎバグ修正確認：特殊状態適用の確認
            if hasattr(defender, '_instance_id') and defender.special_conditions:
                instance_info = getattr(defender, '_instance_id', 'unknown')
                condition_names = [condition.value for condition in defender.special_conditions]
                messages.append(f"(インスタンス {instance_info} の特殊状態: {', '.join(condition_names)})")
            
            return messages
            
        except Exception as e:
            messages.append(f"攻撃効果適用エラー: {e}")
            return messages
    
    @staticmethod
    def validate_pokemon_state(pokemon: Card, location_name: str) -> List[str]:
        """
        ポケモンの状態を検証（HP引き継ぎバグ検証用）
        
        Args:
            pokemon: 検証するポケモン
            location_name: 場所名（例: "バトル場", "ベンチ1"）
            
        Returns:
            検証結果メッセージのリスト
        """
        messages = []
        
        try:
            if not pokemon:
                return ["ポケモンが存在しません"]
            
            instance_info = getattr(pokemon, '_instance_id', 'unknown')
            current_hp = pokemon.current_hp
            damage_taken = pokemon.damage_taken
            
            messages.append(f"{location_name}: {pokemon.name}")
            messages.append(f"  インスタンス: {instance_info}")
            messages.append(f"  HP: {current_hp}/{pokemon.hp} (ダメージ: {damage_taken})")
            
            # 異常な状態のチェック
            if damage_taken < 0:
                messages.append("  ⚠️ 異常: ダメージが負の値です")
            
            if damage_taken > 0 and location_name.startswith("ベンチ"):
                messages.append("  💡 注意: ベンチポケモンにダメージがあります")
            
            if pokemon.special_conditions:
                condition_names = [condition.value for condition in pokemon.special_conditions]
                messages.append(f"  特殊状態: {', '.join(condition_names)}")
            
            return messages
            
        except Exception as e:
            return [f"ポケモン状態検証エラー: {e}"]
    
    @staticmethod
    def ensure_pokemon_independence(pokemon: Card) -> Card:
        """
        ポケモンの独立性を確保（HP引き継ぎバグ完全防止）
        
        Args:
            pokemon: 独立性を確保するポケモン
            
        Returns:
            独立したポケモンインスタンス
        """
        try:
            # 深いコピーで完全に独立したインスタンスを作成
            independent_pokemon = copy.deepcopy(pokemon)
            
            # 状態を確実に初期化（念のため）
            independent_pokemon.damage_taken = 0
            independent_pokemon.special_conditions = set()
            independent_pokemon.attached_energy = []
            independent_pokemon.attached_tools = []
            
            # 新しいインスタンスIDを付与
            if hasattr(pokemon, '_instance_id'):
                original_id = pokemon._instance_id
                independent_pokemon._instance_id = f"{original_id}_copy_{id(independent_pokemon)}"
            
            return independent_pokemon
            
        except Exception as e:
            print(f"ポケモン独立性確保エラー: {e}")
            return pokemon  # エラー時は元のインスタンスを返す