# gui/ai_controller.py
# Version: 4.22
# Updated: 2025-06-10 16:15
# AIコントローラー：無色エネルギーシステム対応版

from typing import List, Optional
import random
from models.game_state import GameState
from models.card import Card, CardType, TrainerType
from utils.energy_cost_checker import EnergyCostChecker
from utils.damage_calculator import DamageCalculator

class AIController:
    """AIの行動を制御するクラス（無色エネルギーシステム対応版）"""
    
    def __init__(self, game_state: GameState, card_actions):
        self.game_state = game_state
        self.card_actions = card_actions
        
        # AI行動回数制限
        self.max_actions_per_turn = 5
        self.current_action_count = 0
        
        # AI戦略フラグ（無色エネルギー対応強化）
        self.prefer_aggressive_play = True  # 攻撃的なプレイを好む
        self.energy_management_priority = 0.8  # エネルギー管理の優先度
        self.colorless_efficiency_weight = 1.2  # 無色エネルギー効率の重み
    
    def execute_ai_turn(self) -> List[str]:
        """AIのターンを実行し、行動メッセージのリストを返す（先攻制限対応版）"""
        messages = []
        
        if self.game_state.current_player != "opponent":
            messages.append("AIのターンではありません。")
            return messages
        
        try:
            print(f"AI行動開始: ターン{self.game_state.turn_count}")
            
            # 🆕 先攻制限チェック表示
            if self.game_state.is_first_player_first_turn():
                print("AI: 先攻最初のターン - 攻撃・サポート使用不可")
            elif self.game_state.is_current_player_first_turn():
                print("AI: 最初のターン - 進化不可")
            else:
                print("AI: 通常ターン - 全アクション可能")
            
            # 行動回数リセット
            self.current_action_count = 0
            
            # AIの行動優先度（先攻制限対応版）
            self._ai_play_basic_pokemon(messages)
            
            if not self.game_state.energy_played_this_turn:
                self._ai_attach_energy_with_colorless_strategy(messages)
            
            self._ai_evolve_pokemon(messages)
            
            # 🆕 先攻制限を考慮したトレーナー使用
            self._ai_use_trainer_cards(messages)
            
            self._ai_execute_attack_with_colorless_consideration(messages)
            
            if not messages or self.current_action_count == 0:
                messages.append("相手は何もできませんでした。")
            
            print(f"AI行動完了: {self.current_action_count}回の行動を実行")
            
        except Exception as e:
            print(f"AI行動エラー: {e}")
            messages.append("相手の行動でエラーが発生しました")
        
        return messages

    def _increment_action_count(self) -> bool:
        """行動回数をカウントし、制限チェック"""
        self.current_action_count += 1
        return self.current_action_count < self.max_actions_per_turn
    
    def _ai_play_basic_pokemon(self, messages: List[str]):
        """AIがたねポケモンを場に出す（従来機能維持）"""
        try:
            # たねポケモンのみを厳密にフィルタリング
            basic_pokemon = [card for card in self.game_state.opponent_hand 
                            if self._is_basic_pokemon(card)]
            
            if not basic_pokemon:
                return
            
            # バトル場が空の場合は最初のポケモンを出す
            if not self.game_state.opponent_active:
                pokemon = basic_pokemon[0]
                self.game_state.opponent_hand.remove(pokemon)
                self.game_state.opponent_active = pokemon
                pokemon.summoned_this_turn = True
                messages.append(f"相手が{pokemon.name}をバトル場に出した。")
                self._increment_action_count()
                return
            
            # ベンチに空きがあればたねポケモンを出す
            for i, slot in enumerate(self.game_state.opponent_bench):
                if slot is None and basic_pokemon and self._increment_action_count():
                    pokemon = basic_pokemon[0]
                    self.game_state.opponent_hand.remove(pokemon)
                    self.game_state.opponent_bench[i] = pokemon
                    pokemon.summoned_this_turn = True
                    messages.append(f"相手が{pokemon.name}をベンチに出した。")
                    basic_pokemon.remove(pokemon)
                    break
        
        except Exception as e:
            print(f"AI基本ポケモン配置エラー: {e}")
    
    def _is_basic_pokemon(self, card: Card) -> bool:
        """カードがたねポケモンかどうかを厳密にチェック"""
        return (card.card_type == CardType.POKEMON and 
                getattr(card, 'evolve_step', 0) == 0)
    
    def _ai_attach_energy_with_colorless_strategy(self, messages: List[str]):
        """AIがエネルギーをつける（v4.22無色エネルギー戦略版）"""
        try:
            if self.game_state.energy_played_this_turn:
                return
            
            energy_cards = [card for card in self.game_state.opponent_hand 
                           if card.card_type == CardType.ENERGY]
            
            if not energy_cards:
                return
            
            # 無色エネルギー戦略に基づく最適対象選択
            best_target = self._select_best_energy_target_with_colorless_strategy()
            
            if best_target and self._increment_action_count():
                energy = energy_cards[0]
                target_location, target_pokemon = best_target
                
                self.game_state.opponent_hand.remove(energy)
                if not hasattr(target_pokemon, 'attached_energy'):
                    target_pokemon.attached_energy = []
                target_pokemon.attached_energy.append(energy)
                
                self.game_state.energy_played_this_turn = True
                
                location_text = "バトル場" if target_location == "active" else "ベンチ"
                energy_type = getattr(energy, 'energy_kind', energy.name)
                messages.append(f"相手が{location_text}の{target_pokemon.name}に{energy_type}エネルギーをつけた。")
        
        except Exception as e:
            print(f"AIエネルギー装着エラー: {e}")
    
    def _select_best_energy_target_with_colorless_strategy(self) -> Optional[tuple]:
        """無色エネルギー戦略に基づく最適なエネルギー装着対象を選択"""
        try:
            candidates = []
            
            # バトル場のポケモンをチェック
            if self.game_state.opponent_active:
                pokemon = self.game_state.opponent_active
                priority = self._calculate_energy_priority_with_colorless(pokemon, "active")
                candidates.append((priority, "active", pokemon))
            
            # ベンチのポケモンをチェック
            for i, pokemon in enumerate(self.game_state.opponent_bench):
                if pokemon:
                    priority = self._calculate_energy_priority_with_colorless(pokemon, "bench")
                    candidates.append((priority, "bench", pokemon))
            
            if not candidates:
                return None
            
            # 最も優先度の高い対象を選択
            candidates.sort(key=lambda x: x[0], reverse=True)
            _, location, pokemon = candidates[0]
            
            return (location, pokemon)
        
        except Exception as e:
            print(f"エネルギー対象選択エラー: {e}")
            return None
    
    def _calculate_energy_priority_with_colorless(self, pokemon: Card, location: str) -> float:
        """無色エネルギーを考慮したポケモンのエネルギー装着優先度を計算"""
        try:
            priority = 0.0
            
            # 基本優先度：バトル場 > ベンチ
            if location == "active":
                priority += 10.0
            else:
                priority += 5.0
            
            # ワザが使用可能になるかチェック（無色エネルギー対応）
            available_attacks = EnergyCostChecker.get_available_attacks(pokemon)
            
            for attack_number, attack_name, can_use, _ in available_attacks:
                if not can_use:
                    # 無色エネルギー効率を考慮した使用可能性判定
                    if self._would_enable_attack_with_colorless_consideration(pokemon, attack_number):
                        priority += 20.0 * self.colorless_efficiency_weight  # 無色エネルギー効率重み適用
                else:
                    priority += 3.0  # 既に使用可能なワザがある場合
            
            # HPの高いポケモンを優先
            if pokemon.hp:
                priority += pokemon.hp * 0.15
            
            # 現在のエネルギー数（少ない方が優先、但し無色エネルギー効率考慮）
            current_energy_count = len(getattr(pokemon, 'attached_energy', []))
            priority -= current_energy_count * 1.5
            
            # 無色エネルギー効率ボーナス（無色コストが多いワザほど優先）
            colorless_efficiency_bonus = self._calculate_colorless_efficiency_bonus(pokemon)
            priority += colorless_efficiency_bonus
            
            return priority
        
        except Exception as e:
            print(f"エネルギー優先度計算エラー: {e}")
            return 0.0
    
    def _calculate_colorless_efficiency_bonus(self, pokemon: Card) -> float:
        """無色エネルギー効率ボーナスを計算"""
        try:
            bonus = 0.0
            
            # ワザ1の無色コスト判定
            if pokemon.attack_name and pokemon.attack_cost_types:
                colorless_cost = 0
                for energy_type, count in pokemon.attack_cost_types.items():
                    if energy_type.lower() in ['colorless', '無色', 'ノーマル']:
                        colorless_cost += count
                
                # 無色コストが多いほどボーナス（任意のエネルギーで支払えるため）
                bonus += colorless_cost * 2.0
            
            # ワザ2の無色コスト判定
            if hasattr(pokemon, 'attack2_name') and pokemon.attack2_name:
                attack2_cost_types = getattr(pokemon, 'attack2_cost_types', {})
                if attack2_cost_types:
                    colorless_cost = 0
                    for energy_type, count in attack2_cost_types.items():
                        if energy_type.lower() in ['colorless', '無色', 'ノーマル']:
                            colorless_cost += count
                    
                    bonus += colorless_cost * 1.5
            
            return bonus
        
        except Exception as e:
            print(f"無色エネルギー効率ボーナス計算エラー: {e}")
            return 0.0
    
    def _would_enable_attack_with_colorless_consideration(self, pokemon: Card, attack_number: int) -> bool:
        """無色エネルギーを考慮してエネルギーを1つ追加したらワザが使用可能になるかチェック"""
        try:
            # 現在のエネルギー状況を取得
            current_energy = EnergyCostChecker._get_attached_energy_summary(pokemon)
            current_total = current_energy.get("total", 0)
            
            # ワザのコスト要求を取得
            if attack_number == 1:
                cost_types = pokemon.attack_cost_types or {}
            else:
                cost_types = getattr(pokemon, 'attack2_cost_types', {}) or {}
            
            if not cost_types:
                return False
            
            total_required = sum(cost_types.values())
            
            # エネルギー1個追加で総数が足りるかチェック
            if current_total + 1 >= total_required:
                # より詳細なチェック：無色エネルギーの柔軟性を考慮
                specific_requirements = {}
                colorless_requirement = 0
                
                for energy_type, count in cost_types.items():
                    if energy_type.lower() in ['colorless', '無色', 'ノーマル']:
                        colorless_requirement += count
                    else:
                        specific_requirements[energy_type] = count
                
                # 特定タイプの要求が満たせるかチェック
                can_meet_specific = True
                for required_type, required_count in specific_requirements.items():
                    if current_energy.get(required_type, 0) < required_count:
                        can_meet_specific = False
                        break
                
                # 特定タイプが満たせる場合、無色コストは任意のエネルギーで支払える
                if can_meet_specific:
                    return True
            
            return False
        
        except Exception as e:
            print(f"ワザ使用可能性チェックエラー: {e}")
            return False
    
    def _ai_evolve_pokemon(self, messages: List[str]):
        """AIがポケモンを進化させる（v4.10進化制限対応版）"""
        try:
            # v4.10強化：進化制限チェック
            if self.game_state.is_current_player_first_turn():
                print("AI: 最初のターンのため進化をスキップします")
                return
            
            evolution_cards = [card for card in self.game_state.opponent_hand 
                              if card.card_type == CardType.POKEMON and card.evolves_from]
            
            for evolution_card in evolution_cards:
                if not self._increment_action_count():
                    break
                
                # バトル場のポケモンをチェック
                if (self.game_state.opponent_active and 
                    evolution_card.can_evolve_from(self.game_state.opponent_active) and
                    self.game_state.can_evolve_pokemon(self.game_state.opponent_active)):
                    
                    self._perform_ai_evolution(evolution_card, "active", None, messages)
                    break
                
                # ベンチのポケモンをチェック
                for i, bench_pokemon in enumerate(self.game_state.opponent_bench):
                    if (bench_pokemon and 
                        evolution_card.can_evolve_from(bench_pokemon) and
                        self.game_state.can_evolve_pokemon(bench_pokemon)):
                        
                        self._perform_ai_evolution(evolution_card, "bench", i, messages)
                        break
        
        except Exception as e:
            print(f"AI進化エラー: {e}")
    
    def _perform_ai_evolution(self, evolution_card: Card, location: str, index: Optional[int], messages: List[str]):
        """AIの進化処理を実行"""
        try:
            self.game_state.opponent_hand.remove(evolution_card)
            
            if location == "active":
                old_pokemon = self.game_state.opponent_active
                self.game_state.opponent_active = evolution_card
            else:
                old_pokemon = self.game_state.opponent_bench[index]
                self.game_state.opponent_bench[index] = evolution_card
            
            # 進化前のポケモンの状態を引き継ぎ
            if hasattr(old_pokemon, 'attached_energy'):
                evolution_card.attached_energy = old_pokemon.attached_energy.copy()
            if hasattr(old_pokemon, 'attached_tools'):
                evolution_card.attached_tools = old_pokemon.attached_tools.copy()
            if hasattr(old_pokemon, 'special_conditions'):
                evolution_card.special_conditions = old_pokemon.special_conditions.copy()
            
            evolution_card.damage_taken = getattr(old_pokemon, 'damage_taken', 0)
            
            location_text = "バトル場" if location == "active" else "ベンチ"
            messages.append(f"相手が{location_text}の{old_pokemon.name}を{evolution_card.name}に進化させた。")
        
        except Exception as e:
            print(f"AI進化実行エラー: {e}")
    

    def _ai_use_trainer_cards(self, messages: List[str]):
        """AIがトレーナーカードを使用（先攻制限対応版）"""
        try:
            # 🆕 先攻制限を含む全体的なサポート使用可能性チェック
            if not self.game_state.can_use_supporter():
                # サポートが使用できない場合、グッズ・スタジアムのみを対象にする
                print("AI: サポート使用制限により、グッズ・スタジアムのみ使用可能")
                self._ai_use_non_supporter_trainers(messages)
                return
            
            trainer_cards = [card for card in self.game_state.opponent_hand 
                            if card.card_type == CardType.TRAINER]
            
            for trainer in trainer_cards:
                if not self._increment_action_count():
                    break
                
                # トレーナータイプ別処理
                if hasattr(trainer, 'trainer_type'):
                    if trainer.trainer_type == TrainerType.SUPPORTER:
                        # サポートの使用
                        if self.game_state.can_use_supporter():
                            self.game_state.opponent_hand.remove(trainer)
                            self.game_state.opponent_discard.append(trainer)
                            self.game_state.supporter_played_this_turn = True
                            messages.append(f"相手が{trainer.name}を使った。")
                            print(f"AI: サポート「{trainer.name}」を使用")
                            break
                        else:
                            # 使用できない理由をログ出力
                            reason = self.game_state.get_supporter_restriction_reason()
                            print(f"AI: サポート「{trainer.name}」使用不可 - {reason}")
                    
                    elif trainer.trainer_type == TrainerType.ITEM:
                        # グッズは制限なし
                        self.game_state.opponent_hand.remove(trainer)
                        self.game_state.opponent_discard.append(trainer)
                        messages.append(f"相手が{trainer.name}を使った。")
                        print(f"AI: グッズ「{trainer.name}」を使用")
                        break
                    
                    elif trainer.trainer_type == TrainerType.STADIUM:
                        # スタジアムは制限なし
                        # 既存スタジアムがある場合はトラッシュ
                        if self.game_state.stadium:
                            old_stadium = self.game_state.stadium
                            self.game_state.opponent_discard.append(old_stadium)
                            print(f"AI: 既存スタジアム「{old_stadium.name}」をトラッシュ")
                        
                        self.game_state.opponent_hand.remove(trainer)
                        self.game_state.stadium = trainer
                        messages.append(f"相手が{trainer.name}を場に出した。")
                        print(f"AI: スタジアム「{trainer.name}」を設置")
                        break
        
        except Exception as e:
            print(f"AIトレーナー使用エラー: {e}")
    
    
    def _ai_use_non_supporter_trainers(self, messages: List[str]):
        """🆕 AIがサポート以外のトレーナーカードを使用"""
        try:
            trainer_cards = [card for card in self.game_state.opponent_hand 
                            if (card.card_type == CardType.TRAINER and 
                                hasattr(card, 'trainer_type') and
                                card.trainer_type != TrainerType.SUPPORTER)]
            
            for trainer in trainer_cards:
                if not self._increment_action_count():
                    break
                
                if trainer.trainer_type == TrainerType.ITEM:
                    # グッズの使用
                    self.game_state.opponent_hand.remove(trainer)
                    self.game_state.opponent_discard.append(trainer)
                    messages.append(f"相手が{trainer.name}を使った。")
                    print(f"AI: グッズ「{trainer.name}」を使用（サポート制限中）")
                    break
                
                elif trainer.trainer_type == TrainerType.STADIUM:
                    # スタジアムの使用
                    if self.game_state.stadium:
                        old_stadium = self.game_state.stadium
                        self.game_state.opponent_discard.append(old_stadium)
                        print(f"AI: 既存スタジアム「{old_stadium.name}」をトラッシュ")
                    
                    self.game_state.opponent_hand.remove(trainer)
                    self.game_state.stadium = trainer
                    messages.append(f"相手が{trainer.name}を場に出した。")
                    print(f"AI: スタジアム「{trainer.name}」を設置（サポート制限中）")
                    break
        
        except Exception as e:
            print(f"AIサポート以外トレーナー使用エラー: {e}")
    

    def _ai_execute_attack_with_colorless_consideration(self, messages: List[str]):
        """AIが攻撃を実行（v4.22無色エネルギー効率考慮版）"""
        try:
            if not self.game_state.opponent_active:
                return
            
            if not self.game_state.player_active:
                return
            
            # 攻撃回数制限チェック
            if not self._increment_action_count():
                return
            
            attacker = self.game_state.opponent_active
            defender = self.game_state.player_active
            
            # 使用可能なワザを取得
            available_attacks = EnergyCostChecker.get_available_attacks(attacker)
            usable_attacks = [(num, name, can_use, details) for num, name, can_use, details in available_attacks if can_use]
            
            if not usable_attacks:
                print("AI: 使用可能なワザがありません")
                return
            
            # 無色エネルギー効率を考慮した最適なワザを選択
            best_attack = self._select_best_attack_with_colorless_consideration(usable_attacks, attacker, defender)
            
            if best_attack:
                attack_number = best_attack[0]
                
                # ワザ使用システムを使って攻撃実行
                attack_messages = DamageCalculator.execute_attack(
                    self.game_state, attacker, defender, attack_number, "opponent"
                )
                
                messages.extend(attack_messages)
                
                print(f"AI攻撃実行: {attacker.name}のワザ{attack_number}（無色エネルギー効率考慮）")
        
        except Exception as e:
            print(f"AI攻撃実行エラー: {e}")
    
    def _select_best_attack_with_colorless_consideration(self, usable_attacks: List[tuple], attacker: Card, defender: Card) -> Optional[tuple]:
        """無色エネルギー効率を考慮した最適なワザを選択"""
        try:
            if not usable_attacks:
                return None
            
            # 各ワザの評価値を計算（無色エネルギー効率考慮）
            attack_scores = []
            
            for attack_number, attack_name, can_use, details in usable_attacks:
                if not can_use:
                    continue
                
                score = self._evaluate_attack_with_colorless_efficiency(attack_number, attacker, defender)
                attack_scores.append((score, attack_number, attack_name, can_use, details))
            
            if not attack_scores:
                return None
            
            # 最も評価の高いワザを選択
            attack_scores.sort(key=lambda x: x[0], reverse=True)
            _, attack_number, attack_name, can_use, details = attack_scores[0]
            
            return (attack_number, attack_name, can_use, details)
        
        except Exception as e:
            print(f"ワザ選択エラー: {e}")
            return usable_attacks[0] if usable_attacks else None
    
    def _evaluate_attack_with_colorless_efficiency(self, attack_number: int, attacker: Card, defender: Card) -> float:
        """無色エネルギー効率を考慮したワザの評価値を計算"""
        try:
            score = 0.0
            
            # ダメージ期待値
            damage, _ = DamageCalculator.calculate_damage(attacker, defender, attack_number)
            score += damage * 1.0
            
            # きぜつ可能性ボーナス
            if defender.hp and damage >= (defender.hp - getattr(defender, 'damage_taken', 0)):
                score += 50.0  # きぜつさせられる場合は大幅ボーナス
            
            # 無色エネルギー効率（無色コストが多いほど効率的と判定）
            if attack_number == 1:
                cost_types = attacker.attack_cost_types or {}
            else:
                cost_types = getattr(attacker, 'attack2_cost_types', {}) or {}
            
            total_cost = sum(cost_types.values())
            colorless_cost = 0
            
            for energy_type, count in cost_types.items():
                if energy_type.lower() in ['colorless', '無色', 'ノーマル']:
                    colorless_cost += count
            
            if total_cost > 0:
                # 無色コストの比率が高いほど効率的（任意のエネルギーで支払えるため）
                colorless_ratio = colorless_cost / total_cost
                score += colorless_ratio * 15.0 * self.colorless_efficiency_weight
                
                # 総エネルギー効率
                efficiency = damage / total_cost if total_cost > 0 else 0
                score += efficiency * 3.0
            
            # ワザの効果ボーナス（簡易版）
            if attack_number == 1:
                effect_text = getattr(attacker, 'attack_effect', '')
            else:
                effect_text = getattr(attacker, 'attack2_effect', '')
            
            if effect_text:
                # 特殊状態付与は追加価値
                if any(condition in effect_text for condition in ["マヒ", "どく", "やけど", "ねむり", "こんらん"]):
                    score += 12.0
            
            return score
        
        except Exception as e:
            print(f"ワザ評価エラー: {e}")
            return 0.0
    
    def get_ai_action_summary(self) -> str:
        """AI行動の要約を取得（無色エネルギー対応版）"""
        return f"AI行動完了: {self.current_action_count}回の行動を実行（無色エネルギー戦略対応）"