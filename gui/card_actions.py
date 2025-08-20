# gui/card_actions.py
# Version: 4.31
# Updated: 2025-06-15 12:10
# カードアクション：マリガン修正版
from typing import List, Optional, Tuple, Any, Dict
import copy

from models.card import Card, CardType, TrainerType  # TrainerTypeを追加
from models.game_state import GameState
from utils.energy_cost_checker import EnergyCostChecker
from utils.damage_calculator import DamageCalculator

class CardActions:
    """カードの行動を処理するクラス（にげるシステム完全実装版）"""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.dialog_manager = None
                
        # 結果管理用の定数
        self.SUCCESS = "success"
        self.FAILURE = "failure"
    
    def set_dialog_manager(self, dialog_manager):
        """ダイアログマネージャーを設定"""
        self.dialog_manager = dialog_manager
    
    def show_message(self, title: str, message: str):
        """メッセージ表示（ダイアログマネージャー使用または標準出力）"""
        if self.dialog_manager:
            self.dialog_manager.show_game_message(title, message)
        else:
            print(f"{title}: {message}")
    
    def retreat_pokemon(self, retreating_pokemon: Card) -> dict:
        """
        ポケモンのにげる処理
        
        Args:
            retreating_pokemon: にげるポケモン
            
        Returns:
            dict: 処理結果
                - success: 成功/失敗
                - message: メッセージ
                - requires_choice: 選択が必要かどうか
                - bench_options: ベンチポケモンの選択肢
                - retreat_cost: にげるコスト
        """
        try:
            print(f"🏃 にげる処理開始: {retreating_pokemon.name}")
            
            # 1. 基本条件チェック
            validation_result = self._validate_retreat_conditions(retreating_pokemon)
            if not validation_result["success"]:
                return validation_result
            
            # 2. にげるコストチェック
            cost_result = self._check_retreat_cost(retreating_pokemon)
            if not cost_result["success"]:
                return cost_result
            
            # 3. ベンチポケモン選択肢を取得
            bench_options = self._get_bench_replacement_options()
            if not bench_options:
                return {
                    "success": False,
                    "message": "ベンチに交代できるポケモンがいません"
                }
            
            # 4. 複数選択肢がある場合は選択が必要
            if len(bench_options) > 1:
                return {
                    "success": False,
                    "message": "交代するポケモンを選択してください",
                    "requires_choice": True,
                    "bench_options": bench_options,
                    "retreat_cost": getattr(retreating_pokemon, 'retreat_cost', 0) or 0
                }
            
            # 5. 自動的に交代実行（選択肢が1つの場合）
            return self._execute_retreat(retreating_pokemon, bench_options[0])
        
        except Exception as e:
            print(f"にげる処理エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"にげる処理中にエラーが発生しました: {e}"
            }
    
    def _validate_retreat_conditions(self, pokemon: Card) -> dict:
        """にげるための基本条件をチェック"""
        try:
            # バトル場のポケモンかチェック
            if pokemon != self.game_state.player_active:
                return {
                    "success": False,
                    "message": "バトル場のポケモンのみがにげることができます"
                }
            
            # プレイヤーのターンかチェック
            if self.game_state.current_player != "player":
                return {
                    "success": False,
                    "message": "自分のターンでのみにげることができます"
                }
            
            # 特殊状態による制限チェック
            from utils.special_condition_helper import SpecialConditionHelper
            can_retreat, reason = SpecialConditionHelper.can_retreat(pokemon)
            if not can_retreat:
                return {
                    "success": False,
                    "message": reason
                }
            
            return {"success": True}
        
        except Exception as e:
            print(f"にげる条件チェックエラー: {e}")
            return {
                "success": False,
                "message": f"にげる条件のチェック中にエラーが発生しました: {e}"
            }
    
    def _check_retreat_cost(self, pokemon: Card) -> dict:
        """にげるコストをチェック"""
        try:
            retreat_cost = getattr(pokemon, 'retreat_cost', 0) or 0
            
            if retreat_cost == 0:
                return {"success": True, "message": "にげるコストはありません"}
            
            # 装着されているエネルギーを取得
            attached_energy = getattr(pokemon, 'attached_energy', [])
            attached_count = len(attached_energy)
            
            if attached_count < retreat_cost:
                return {
                    "success": False,
                    "message": f"にげるコストが不足しています（必要: {retreat_cost}個、装着: {attached_count}個）"
                }
            
            return {
                "success": True,
                "message": f"にげるコスト: {retreat_cost}個のエネルギーを支払います"
            }
        
        except Exception as e:
            print(f"にげるコストチェックエラー: {e}")
            return {
                "success": False,
                "message": f"にげるコストのチェック中にエラーが発生しました: {e}"
            }
    
    def _get_bench_replacement_options(self) -> List[Tuple[int, Card]]:
        """ベンチから交代可能なポケモンの選択肢を取得"""
        try:
            options = []
            for i, bench_pokemon in enumerate(self.game_state.player_bench):
                if bench_pokemon is not None:
                    options.append((i, bench_pokemon))
            
            print(f"交代可能なベンチポケモン: {len(options)}匹")
            return options
        
        except Exception as e:
            print(f"ベンチ選択肢取得エラー: {e}")
            return []
    
    def _execute_retreat(self, retreating_pokemon: Card, bench_choice: Tuple[int, Card]) -> dict:
        """にげる処理を実行"""
        try:
            bench_index, replacement_pokemon = bench_choice
            retreat_cost = getattr(retreating_pokemon, 'retreat_cost', 0) or 0
            
            print(f"🏃 にげる実行: {retreating_pokemon.name} → {replacement_pokemon.name}")
            
            # 1. エネルギーコストを支払う
            if retreat_cost > 0:
                cost_paid = self._pay_retreat_cost(retreating_pokemon, retreat_cost)
                if not cost_paid:
                    return {
                        "success": False,
                        "message": "エネルギーコストの支払いに失敗しました"
                    }
            
            # 2. ポケモンを交代
            self.game_state.player_active = replacement_pokemon
            self.game_state.player_bench[bench_index] = retreating_pokemon
            
            # 3. 結果メッセージ作成
            message_parts = [f"{retreating_pokemon.name}がにげました"]
            if retreat_cost > 0:
                message_parts.append(f"エネルギー{retreat_cost}個を支払いました")
            message_parts.append(f"{replacement_pokemon.name}がバトル場に出ました")
            
            print("✅ にげる処理完了")
            
            return {
                "success": True,
                "message": "\n".join(message_parts)
            }
        
        except Exception as e:
            print(f"にげる実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"にげる実行中にエラーが発生しました: {e}"
            }
    
    def _pay_retreat_cost(self, pokemon: Card, cost: int) -> bool:
        """にげるコストとしてエネルギーを支払う"""
        try:
            attached_energy = getattr(pokemon, 'attached_energy', [])
            
            if len(attached_energy) < cost:
                print(f"エネルギー不足: 必要{cost}個、装着{len(attached_energy)}個")
                return False
            
            # エネルギーを捨て札に送る（後ろから取る）
            for _ in range(cost):
                if attached_energy:
                    discarded_energy = attached_energy.pop()
                    self.game_state.player_discard.append(discarded_energy)
                    print(f"エネルギーを捨て札に: {discarded_energy.name}")
            
            return True
        
        except Exception as e:
            print(f"エネルギー支払いエラー: {e}")
            return False
    
    def retreat_pokemon_with_choice(self, retreating_pokemon: Card, bench_index: int) -> dict:
        """
        選択されたベンチポケモンとの交代でにげる処理を実行
        
        Args:
            retreating_pokemon: にげるポケモン
            bench_index: 交代するベンチポケモンのインデックス
        """
        try:
            # ベンチポケモンの存在確認
            if bench_index < 0 or bench_index >= len(self.game_state.player_bench):
                return {
                    "success": False,
                    "message": "無効なベンチポケモンが選択されました"
                }
            
            replacement_pokemon = self.game_state.player_bench[bench_index]
            if not replacement_pokemon:
                return {
                    "success": False,
                    "message": "選択されたベンチスロットにポケモンがいません"
                }
            
            # にげる処理を実行
            return self._execute_retreat(retreating_pokemon, (bench_index, replacement_pokemon))
        
        except Exception as e:
            print(f"選択的にげる処理エラー: {e}")
            return {
                "success": False,
                "message": f"にげる処理中にエラーが発生しました: {e}"
            }
    
    def use_pokemon_attack(self, pokemon_position: str, attack_number: int) -> Dict:
        """ポケモンの攻撃を実行（1ベース攻撃番号対応版）"""
        try:
            print(f"攻撃実行開始: 位置={pokemon_position}, ワザ番号={attack_number}")
            
            # ポケモンの取得
            if pokemon_position == "active":
                attacking_pokemon = self.game_state.player_active
            elif pokemon_position.startswith("bench_"):
                bench_index = int(pokemon_position.split("_")[1])
                attacking_pokemon = self.game_state.player_bench[bench_index]
            else:
                return {
                    "success": False,
                    "message": "無効なポケモンの位置です"
                }
            
            if not attacking_pokemon:
                return {
                    "success": False,
                    "message": "指定されたポケモンが見つかりません"
                }
            
            print(f"攻撃ポケモン: {attacking_pokemon.name}")
            
            # ワザの存在チェック（1ベース対応）
            if attack_number == 1:
                if not hasattr(attacking_pokemon, 'attack_name') or not attacking_pokemon.attack_name:
                    return {
                        "success": False,
                        "message": "ワザ1が設定されていません"
                    }
                attack_name = attacking_pokemon.attack_name
                attack_power = getattr(attacking_pokemon, 'attack_power', 0) or 0
            elif attack_number == 2:
                if not hasattr(attacking_pokemon, 'attack2_name') or not attacking_pokemon.attack2_name:
                    return {
                        "success": False,
                        "message": "ワザ2が設定されていません"
                    }
                attack_name = attacking_pokemon.attack2_name
                attack_power = getattr(attacking_pokemon, 'attack2_power', 0) or 0
            else:
                return {
                    "success": False,
                    "message": "無効なワザ番号です（1または2を指定してください）"
                }
            
            print(f"使用ワザ: {attack_name} (ダメージ: {attack_power})")
            
            # エネルギーコスト判定
            from utils.energy_cost_checker import EnergyCostChecker
            can_use, cost_message = EnergyCostChecker.can_use_attack(attacking_pokemon, attack_number, self.game_state)
            
            if not can_use:
                return {
                    "success": False,
                    "message": f"「{attack_name}」は使用できません: {cost_message}"
                }
            
            print(f"エネルギーコスト判定: OK - {cost_message}")
            
            # 攻撃対象の取得
            target_pokemon = self.game_state.opponent_active
            if not target_pokemon:
                return {
                    "success": False,
                    "message": "攻撃対象が見つかりません"
                }
            
            print(f"攻撃対象: {target_pokemon.name}")
            
            # ダメージ計算
            from utils.damage_calculator import DamageCalculator
            actual_damage, damage_messages = DamageCalculator.calculate_damage(
                attacking_pokemon, target_pokemon, attack_number
            )
            
            print(f"計算ダメージ: {actual_damage}")
            
            # ダメージ適用
            is_knocked_out, apply_messages = DamageCalculator.apply_damage(
                target_pokemon, actual_damage
            )
            
            # メッセージ作成
            result_messages = []
            result_messages.append(f"{attacking_pokemon.name}の「{attack_name}」！")
            result_messages.extend(damage_messages)
            result_messages.extend(apply_messages)
            
            # きぜつ処理
            if is_knocked_out:
                print(f"{target_pokemon.name}がきぜつしました")
                
                # 相手のバトル場をクリア
                self.game_state.opponent_active = None
                
                # 捨て札に送る
                self.game_state.opponent_discard.append(target_pokemon)
                
                # 相手のベンチから新しいポケモンを出す（簡易AI）
                for i, bench_pokemon in enumerate(self.game_state.opponent_bench):
                    if bench_pokemon:
                        self.game_state.opponent_active = bench_pokemon
                        self.game_state.opponent_bench[i] = None
                        result_messages.append(f"相手が{bench_pokemon.name}をバトル場に出しました")
                        print(f"相手の新バトルポケモン: {bench_pokemon.name}")
                        break
                
                # サイド獲得処理（簡易実装）
                if self.game_state.opponent_prizes:
                    side_card = self.game_state.opponent_prizes.pop(0)
                    self.game_state.player_hand.append(side_card)
                    result_messages.append("サイドを1枚獲得しました")
                    print("サイド獲得")
            
            # 攻撃完了処理
            self.game_state.mark_attack_completed()
            print("攻撃完了マーク設定")
            
            return {
                "success": True,
                "message": "\n".join(result_messages),
                "damage_dealt": actual_damage,
                "target_knocked_out": is_knocked_out
            }
        
        except Exception as e:
            print(f"攻撃実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"攻撃実行中にエラーが発生しました: {e}"
            }

    def _get_pokemon_attacks(self, pokemon: Card) -> List[dict]:
        """ポケモンのワザ情報を安全に取得（旧形式優先版）"""
        try:
            attacks = []
            
            # 旧形式を優先してチェック（実際のカードデータ形式）
            if hasattr(pokemon, 'attack_name') and pokemon.attack_name:
                attack1 = {
                    'name': pokemon.attack_name,
                    'damage': getattr(pokemon, 'attack_power', ''),
                    'cost': getattr(pokemon, 'attack_cost_types', {}),
                    'description': getattr(pokemon, 'attack_effect', '')
                }
                attacks.append(attack1)
                print(f"ワザ1取得: {attack1['name']} (ダメージ: {attack1['damage']})")
            
            if hasattr(pokemon, 'attack2_name') and pokemon.attack2_name:
                attack2 = {
                    'name': pokemon.attack2_name,
                    'damage': getattr(pokemon, 'attack2_power', ''),
                    'cost': getattr(pokemon, 'attack2_cost_types', {}),
                    'description': getattr(pokemon, 'attack2_effect', '')
                }
                attacks.append(attack2)
                print(f"ワザ2取得: {attack2['name']} (ダメージ: {attack2['damage']})")
            
            # 新形式も確認（フォールバック）
            if not attacks and hasattr(pokemon, 'attacks') and pokemon.attacks and len(pokemon.attacks) > 0:
                attacks = pokemon.attacks
                print(f"新形式ワザ取得: {len(attacks)}個")
            
            print(f"{pokemon.name}のワザ数: {len(attacks)}")
            return attacks
        
        except Exception as e:
            print(f"ワザ取得エラー: {e}")
            return []
    
    def use_ability(self, pokemon: Card) -> str:
        """特性使用処理（未実装）"""
        try:
            if not hasattr(pokemon, 'ability_name') or not pokemon.ability_name:
                return f"{pokemon.name}には特性がありません"
            
            # 特性使用処理は未実装
            return f"{pokemon.ability_name}の使用は未実装です"
        
        except Exception as e:
            print(f"特性使用エラー: {e}")
            return "特性使用中にエラーが発生しました"
    
    def play_card_from_hand(self, card_index: int) -> str:
        """手札からカードを使用"""
        try:
            if card_index >= len(self.game_state.player_hand):
                return "指定されたカードが見つかりません"
            
            card = self.game_state.player_hand[card_index]
            
            if card.card_type == CardType.POKEMON:
                return self._handle_pokemon_play(card, card_index)
            elif card.card_type == CardType.ENERGY:
                return self._handle_energy_play(card, card_index)
            elif card.card_type == CardType.TRAINER:
                return self._handle_trainer_play(card, card_index)
            else:
                return f"{card.card_type}カードの使用は未実装です"
        
        except Exception as e:
            return f"カード使用エラー: {e}"
    
    def _handle_pokemon_play(self, pokemon_card: Card, card_index: int) -> str:
        """ポケモンカードの使用処理（進化制限ルール修正版）"""
        try:
            # 🆕 進化可能性チェック（ゲームルール準拠）
            evolution_targets = self._get_evolution_targets_with_rule_check(pokemon_card)
            
            if evolution_targets:
                # 進化可能な場合
                target_location, target_index, target_pokemon = evolution_targets[0]  # 最初のターゲットを使用
                return self._evolve_pokemon(pokemon_card, card_index, target_location, target_index, target_pokemon)
            else:
                # ベンチに出す（たねポケモンの場合）
                if getattr(pokemon_card, 'evolve_step', 0) == 0:
                    return self._place_pokemon_on_bench(pokemon_card, card_index)
                else:
                    return f"{pokemon_card.name}は進化ポケモンです。進化元のポケモンが場にいないか、進化制限により進化できません。"
        
        except Exception as e:
            return f"ポケモンカード使用エラー: {e}"

    def _get_evolution_targets_with_rule_check(self, pokemon_card: Card) -> List[Tuple[str, int, Card]]:
        """進化可能なポケモンを取得（ゲームルール準拠チェック付き）"""
        targets = []
        try:
            if not pokemon_card.evolves_from:
                return targets
            
            print(f"🧬 進化チェック開始: {pokemon_card.name} ← {pokemon_card.evolves_from}")
            
            # バトル場をチェック
            if (self.game_state.player_active and 
                self.game_state.player_active.name == pokemon_card.evolves_from):
                
                # 🆕 ゲームルールに基づく進化可能性チェック
                if self.game_state.can_evolve_pokemon(self.game_state.player_active):
                    targets.append(("active", 0, self.game_state.player_active))
                    print(f"✅ バトル場の{self.game_state.player_active.name}は進化可能")
                else:
                    print(f"❌ バトル場の{self.game_state.player_active.name}は進化制限により進化不可")
            
            # ベンチをチェック
            for i, bench_pokemon in enumerate(self.game_state.player_bench):
                if bench_pokemon and bench_pokemon.name == pokemon_card.evolves_from:
                    
                    # 🆕 ゲームルールに基づく進化可能性チェック
                    if self.game_state.can_evolve_pokemon(bench_pokemon):
                        targets.append(("bench", i, bench_pokemon))
                        print(f"✅ ベンチ{i+1}の{bench_pokemon.name}は進化可能")
                    else:
                        print(f"❌ ベンチ{i+1}の{bench_pokemon.name}は進化制限により進化不可")
            
            print(f"🧬 進化可能対象数: {len(targets)}")
        
        except Exception as e:
            print(f"進化対象取得エラー: {e}")
        
        return targets

    
    def _handle_energy_play(self, energy_card: Card, card_index: int) -> str:
        """エネルギーカードの使用処理（1ターン1回制限対応版）"""
        try:
            # 🆕 エネルギー装着1ターン1回制限チェック
            if self.game_state.energy_played_this_turn:
                return "このターンはすでにエネルギーを装着しました。エネルギーの装着は1ターンに1回までです。"
            
            # エネルギー装着可能なポケモンを取得
            pokemon_targets = self._get_energy_targets()
            
            if not pokemon_targets:
                return "エネルギーを装着できるポケモンがいません"
            
            # ダイアログで装着対象を選択
            if self.dialog_manager:
                self.dialog_manager.show_pokemon_selection_for_energy(
                    energy_card, pokemon_targets,
                    lambda selected: self._attach_energy_callback(energy_card, card_index, selected)
                )
                return "エネルギー装着対象を選択してください"
            else:
                # ダイアログマネージャーがない場合は最初のポケモンに装着
                location, index = pokemon_targets[0][:2]
                return self._attach_energy_to_pokemon(energy_card, card_index, location, index)
        
        except Exception as e:
            return f"エネルギーカード使用エラー: {e}"

    def _handle_trainer_play(self, trainer_card: Card, card_index: int) -> str:
        """トレーナーカードの使用処理（公式ルール準拠版）"""
        try:
            # トレーナータイプを取得
            trainer_type = getattr(trainer_card, 'trainer_type', None)
            
            if not trainer_type:
                # trainer_typeが設定されていない場合はカード名から推定
                trainer_type = self._detect_trainer_type_from_name(trainer_card.name)
            
            print(f"トレーナーカード使用: {trainer_card.name} (タイプ: {trainer_type})")
            
            # タイプ別処理
            if trainer_type == "supporter" or trainer_type == TrainerType.SUPPORTER:
                return self._handle_supporter_play(trainer_card, card_index)
            elif trainer_type == "item" or trainer_type == TrainerType.ITEM:
                return self._handle_item_play(trainer_card, card_index)  
            elif trainer_type == "stadium" or trainer_type == TrainerType.STADIUM:
                return self._handle_stadium_play(trainer_card, card_index)
            else:
                # 不明なタイプの場合はグッズとして扱う
                print(f"警告: {trainer_card.name}のタイプが不明です。グッズとして処理します。")
                return self._handle_item_play(trainer_card, card_index)
        
        except Exception as e:
            return f"トレーナーカード使用エラー: {e}"
    
 
    def _handle_supporter_play(self, supporter_card: Card, card_index: int) -> str:
        """サポートカードの使用処理（公式ルール準拠版）"""
        try:
            # 🆕 サポート使用制限チェック（先攻制限含む）
            if not self.game_state.can_use_supporter():
                restriction_reason = self.game_state.get_supporter_restriction_reason()
                return f"{supporter_card.name}を使用できません。{restriction_reason}"
            
            # 手札からトラッシュへ移動
            if self._move_card_from_hand_to_discard(card_index):
                # サポート使用フラグを設定
                self.game_state.supporter_played_this_turn = True
                
                # 効果処理は今後実装
                effect_message = self._apply_supporter_effect(supporter_card)
                
                return f"{supporter_card.name}を使用しました。{effect_message}"
            else:
                return f"{supporter_card.name}の使用に失敗しました。"
        
        except Exception as e:
            return f"サポートカード使用エラー: {e}"
            
    def _handle_item_play(self, item_card: Card, card_index: int) -> str:
        """グッズカードの使用処理（制限なし）"""
        try:
            # グッズには使用回数制限なし
            
            # 手札からトラッシュへ移動
            if self._move_card_from_hand_to_discard(card_index):
                # 効果処理は今後実装
                effect_message = self._apply_item_effect(item_card)
                
                return f"{item_card.name}を使用しました。{effect_message}"
            else:
                return f"{item_card.name}の使用に失敗しました。"
        
        except Exception as e:
            return f"グッズカード使用エラー: {e}"
    
    def _handle_stadium_play(self, stadium_card: Card, card_index: int) -> str:
        """スタジアムカードの使用処理"""
        try:
            # 既存のスタジアムがある場合の処理
            previous_stadium = None
            if self.game_state.stadium:
                previous_stadium = self.game_state.stadium
                # 既存スタジアムをトラッシュへ
                self.game_state.player_discard.append(previous_stadium)
                print(f"既存のスタジアム「{previous_stadium.name}」をトラッシュしました")
            
            # 手札からスタジアムエリアへ移動
            if self._move_card_from_hand_to_stadium(card_index, stadium_card):
                # 効果処理は今後実装
                effect_message = self._apply_stadium_effect(stadium_card)
                
                if previous_stadium:
                    return f"{stadium_card.name}を場に出しました。{previous_stadium.name}はトラッシュされました。{effect_message}"
                else:
                    return f"{stadium_card.name}を場に出しました。{effect_message}"
            else:
                return f"{stadium_card.name}の使用に失敗しました。"
        
        except Exception as e:
            return f"スタジアムカード使用エラー: {e}"

    def _move_card_from_hand_to_discard(self, card_index: int) -> bool:
        """手札からトラッシュへカードを移動"""
        try:
            if card_index >= len(self.game_state.player_hand):
                print(f"無効なカードインデックス: {card_index}")
                return False
            
            # カードを手札から削除してトラッシュへ追加
            card = self.game_state.player_hand.pop(card_index)
            self.game_state.player_discard.append(card)
            
            print(f"カード移動: {card.name} → トラッシュ")
            return True
        
        except Exception as e:
            print(f"カード移動エラー: {e}")
            return False
    
    def _move_card_from_hand_to_stadium(self, card_index: int, stadium_card: Card) -> bool:
        """手札からスタジアムエリアへカードを移動"""
        try:
            if card_index >= len(self.game_state.player_hand):
                print(f"無効なカードインデックス: {card_index}")
                return False
            
            # カードを手札から削除してスタジアムエリアへ設定
            card = self.game_state.player_hand.pop(card_index)
            self.game_state.stadium = card
            
            print(f"スタジアム設置: {card.name}")
            return True
        
        except Exception as e:
            print(f"スタジアム設置エラー: {e}")
            return False
    
    def _detect_trainer_type_from_name(self, card_name: str) -> str:
        """カード名からトレーナータイプを推定（暫定実装）"""
        # よくあるサポートカード名のパターン
        supporter_keywords = ["博士", "ジム", "リーダー", "チャンピオン", "研究員", "助手"]
        
        # よくあるスタジアム名のパターン  
        stadium_keywords = ["スタジアム", "ジム", "センター", "タワー", "島", "山", "森", "湖", "遺跡"]
        
        card_name_lower = card_name.lower()
        
        for keyword in supporter_keywords:
            if keyword in card_name:
                return "supporter"
        
        for keyword in stadium_keywords:
            if keyword in card_name:
                return "stadium"
        
        # どちらにも該当しない場合はグッズとして扱う
        return "item"
    
    def _apply_supporter_effect(self, supporter_card: Card) -> str:
        """サポートカードの効果を適用（今後実装）"""
        # 現在は効果未実装のため、基本メッセージのみ
        return "効果はまだ実装されていません。"
    
    def _apply_item_effect(self, item_card: Card) -> str:
        """グッズカードの効果を適用（今後実装）"""
        # 現在は効果未実装のため、基本メッセージのみ
        return "効果はまだ実装されていません。"
    
    def _apply_stadium_effect(self, stadium_card: Card) -> str:
        """スタジアムカードの効果を適用（今後実装）"""
        # 現在は効果未実装のため、基本メッセージのみ
        return "効果はまだ実装されていません。"

    def _get_evolution_targets(self, pokemon_card: Card) -> List[Tuple[str, int]]:
        """進化可能なポケモンを取得"""
        targets = []
        try:
            if not pokemon_card.evolves_from:
                return targets
            
            # バトル場をチェック
            if (self.game_state.player_active and 
                self.game_state.player_active.name == pokemon_card.evolves_from):
                targets.append(("active", 0))
            
            # ベンチをチェック
            for i, bench_pokemon in enumerate(self.game_state.player_bench):
                if bench_pokemon and bench_pokemon.name == pokemon_card.evolves_from:
                    targets.append(("bench", i))
        
        except Exception as e:
            print(f"進化対象取得エラー: {e}")
        
        return targets
    
    def _get_energy_targets(self) -> List[Tuple[str, Optional[int], Card]]:
        """エネルギー装着可能なポケモンを取得"""
        targets = []
        try:
            # バトル場
            if self.game_state.player_active:
                targets.append(("active", None, self.game_state.player_active))
            
            # ベンチ
            for i, bench_pokemon in enumerate(self.game_state.player_bench):
                if bench_pokemon:
                    targets.append(("bench", i, bench_pokemon))
        
        except Exception as e:
            print(f"エネルギー対象取得エラー: {e}")
        
        return targets
    
    def _evolve_pokemon(self, evolution_card: Card, card_index: int, 
                       target_location: str, target_index: int, target_pokemon: Card) -> str:
        """ポケモンの進化処理（進化制限ルール修正版）"""
        try:
            print(f"🧬 進化実行: {target_pokemon.name} → {evolution_card.name}")
            
            # 🆕 再度進化可能性チェック（二重チェック）
            if not self.game_state.can_evolve_pokemon(target_pokemon):
                return f"{target_pokemon.name}は現在進化できません（進化制限により）"
            
            # 進化前ポケモンの状態を進化後に引き継ぎ
            evolution_card.damage_taken = getattr(target_pokemon, 'damage_taken', 0)
            
            if hasattr(target_pokemon, 'attached_energy'):
                evolution_card.attached_energy = target_pokemon.attached_energy.copy()
            else:
                evolution_card.attached_energy = []
            
            if hasattr(target_pokemon, 'attached_tools'):
                evolution_card.attached_tools = target_pokemon.attached_tools.copy()
            else:
                evolution_card.attached_tools = []
            
            if hasattr(target_pokemon, 'special_conditions'):
                evolution_card.special_conditions = target_pokemon.special_conditions.copy()
            else:
                evolution_card.special_conditions = set()
            
            # 🆕 進化したポケモンのsummoned_this_turnフラグを設定
            evolution_card.summoned_this_turn = False
            evolution_card.evolved_this_turn = True
            
            # 場所に応じて配置
            if target_location == "active":
                self.game_state.player_active = evolution_card
            elif target_location == "bench":
                self.game_state.player_bench[target_index] = evolution_card
            
            # 手札から進化カードを削除し、進化前ポケモンを捨て札に
            self.game_state.player_hand.pop(card_index)
            self.game_state.player_discard.append(target_pokemon)
            
            print(f"✅ 進化完了: {target_pokemon.name} → {evolution_card.name}")
            return f"{target_pokemon.name}を{evolution_card.name}に進化させました"
        
        except Exception as e:
            print(f"進化処理エラー: {e}")
            return f"進化処理エラー: {e}"


    def _place_pokemon_on_bench(self, pokemon_card: Card, card_index: int) -> str:
        """ポケモンをベンチに配置（summoned_this_turnフラグ設定強化版）"""
        try:
            # ポケモンカードかチェック
            if pokemon_card.card_type != CardType.POKEMON:
                return f"{pokemon_card.name}はポケモンカードではありません"
            
            # たねポケモンかチェック
            if getattr(pokemon_card, 'evolve_step', 0) != 0:
                return f"{pokemon_card.name}は進化ポケモンです。進化元となるポケモンを場に出してから進化させてください。"
            
            # 空いているベンチスロットを探す
            for i in range(5):  # ベンチは最大5匹
                if i >= len(self.game_state.player_bench) or not self.game_state.player_bench[i]:
                    # 空きスロットに配置
                    while len(self.game_state.player_bench) <= i:
                        self.game_state.player_bench.append(None)
                    
                    self.game_state.player_bench[i] = pokemon_card
                    self.game_state.player_hand.pop(card_index)
                    
                    # 🆕 summoned_this_turnフラグを設定（そのターンに出されたため進化不可）
                    pokemon_card.summoned_this_turn = True
                    self.game_state.set_pokemon_summoned_this_turn(pokemon_card, True)
                    
                    print(f"✅ ベンチ配置: {pokemon_card.name} (summoned_this_turn=True)")
                    return f"{pokemon_card.name}をベンチに出しました"
            
            return "ベンチが満杯です"
    
        except Exception as e:
            return f"ベンチ配置エラー: {e}"

    def _attach_energy_callback(self, energy_card: Card, card_index: int, selected: Optional[Tuple[str, Optional[int]]]):
        """エネルギー装着コールバック"""
        try:
            if selected:
                location, index = selected
                result = self._attach_energy_to_pokemon(energy_card, card_index, location, index)
                self.show_message("エネルギー装着", result)
                
                # 🔥 バグ修正：UI更新を追加
                if hasattr(self, 'update_display_callback') and self.update_display_callback:
                    self.update_display_callback()
        
        except Exception as e:
            self.show_message("エラー", f"エネルギー装着コールバックエラー: {e}")

    def _attach_energy_to_pokemon(self, energy_card: Card, card_index: int, 
                                location: str, index: Optional[int]) -> str:
        """指定されたポケモンにエネルギーを装着（1ターン1回制限対応版）"""
        try:
            # 🆕 エネルギー装着1ターン1回制限チェック（二重チェック）
            if self.game_state.energy_played_this_turn:
                return "このターンはすでにエネルギーを装着しました。エネルギーの装着は1ターンに1回までです。"
            
            # 対象ポケモンを取得
            if location == "active":
                target_pokemon = self.game_state.player_active
            elif location == "bench":
                target_pokemon = self.game_state.player_bench[index]
            else:
                return "無効な装着位置です"
            
            if not target_pokemon:
                return "対象のポケモンが見つかりません"
            
            # エネルギーを装着
            if not hasattr(target_pokemon, 'attached_energy'):
                target_pokemon.attached_energy = []
            
            target_pokemon.attached_energy.append(energy_card)
            self.game_state.player_hand.pop(card_index)
            
            # 🆕 エネルギー装着フラグを設定
            self.game_state.energy_played_this_turn = True
            print(f"✅ エネルギー装着フラグ設定: energy_played_this_turn = True")
            
            return f"{target_pokemon.name}に{energy_card.name}を装着しました"
        
        except Exception as e:
            return f"エネルギー装着エラー: {e}"