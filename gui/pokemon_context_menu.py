# gui/pokemon_context_menu.py
# Version: 4.31
# Updated: 2025-06-14 12:20
# ポケモンコンテキストメニュー：にげるシステム完全統合版

import tkinter as tk
from tkinter import Menu
from typing import Callable, Optional, List, Tuple
from models.card import Card
from models.game_state import GameState

class PokemonContextMenu:
    """ポケモン用統一コンテキストメニューシステム（にげるシステム完全統合版）"""
    
    def __init__(self, parent_widget: tk.Widget, game_state: GameState):
        self.parent = parent_widget
        self.game_state = game_state
        self.current_menu = None
        
        # 現在のポケモン位置情報
        self.current_pokemon_position: Optional[Tuple[str, str, Optional[int]]] = None
        
        # コールバック関数
        self.attack_callback: Optional[Callable[[Card, int], None]] = None
        self.ability_callback: Optional[Callable[[Card], None]] = None
        self.retreat_callback: Optional[Callable[[Card], None]] = None
        self.details_callback: Optional[Callable[[Card], None]] = None
    
    def set_callbacks(self,
                     attack_callback: Optional[Callable[[Card, int], None]] = None,
                     ability_callback: Optional[Callable[[Card], None]] = None,
                     retreat_callback: Optional[Callable[[Card], None]] = None,
                     details_callback: Optional[Callable[[Card], None]] = None):
        """コールバック関数を設定"""
        self.attack_callback = attack_callback
        self.ability_callback = ability_callback
        self.retreat_callback = retreat_callback
        self.details_callback = details_callback
    
    def set_current_position(self, side: str, location: str, index: Optional[int]):
        """現在のポケモン位置情報を設定"""
        self.current_pokemon_position = (side, location, index)
        print(f"コンテキストメニュー位置設定: {side}-{location}-{index}")
    
    def show_pokemon_menu(self, event, pokemon: Card, owner: str = "player"):
        """ポケモンのコンテキストメニューを表示"""
        try:
            # 既存のメニューを破棄
            if self.current_menu:
                try:
                    self.current_menu.destroy()
                except:
                    pass
                self.current_menu = None
            
            # 新しいメニューを作成
            menu = Menu(self.parent, tearoff=0)
            self.current_menu = menu
            
            # プレイヤーのポケモンのみメニューを表示
            if owner != "player":
                return
            
            # ターン制限チェック
            if self.game_state.current_player != "player":
                menu.add_command(
                    label="相手のターンです",
                    state="disabled"
                )
                menu.tk_popup(event.x_root, event.y_root)
                return
            
            menu_added = False
            
            # 1. ワザメニュー（先攻1ターン目攻撃制限対応）
            attack_menus = self._add_attack_menus(menu, pokemon)
            if attack_menus:
                menu_added = True
            
            # 2. 特性メニュー
            if self._add_ability_menu(menu, pokemon):
                if menu_added:
                    menu.add_separator()
                menu_added = True
            
            # 3. にげるメニュー（🆕 v4.31完全実装）
            if self._add_retreat_menu(menu, pokemon):
                if menu_added:
                    menu.add_separator()
                menu_added = True
            
            # 4. カード詳細メニュー
            if menu_added:
                menu.add_separator()
            
            menu.add_command(
                label="📋 カード詳細",
                command=lambda: self._on_details_selected(pokemon)
            )
            
            # メニューが空でない場合に表示
            if menu_added or True:  # 詳細は常に表示
                menu.tk_popup(event.x_root, event.y_root)
        
        except Exception as e:
            print(f"コンテキストメニュー表示エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_attack_menus(self, menu: Menu, pokemon: Card) -> bool:
        """ワザメニューを追加（旧形式カードデータ対応版）"""
        try:
            # 先攻1ターン目攻撃制限チェック
            first_turn_restriction = self.game_state.is_first_player_first_turn()
            
            # 攻撃済みチェック
            already_attacked = getattr(self.game_state, 'player_has_attacked', False)
            
            # 旧形式のワザ情報を取得
            attacks_found = False
            
            # ワザ1のチェック
            if hasattr(pokemon, 'attack_name') and pokemon.attack_name:
                attacks_found = True
                attack_name = pokemon.attack_name
                attack_power = getattr(pokemon, 'attack_power', 0) or 0
                
                # エネルギーコスト表示
                cost_types = getattr(pokemon, 'attack_cost_types', {}) or {}
                total_cost = sum(cost_types.values()) if cost_types else 0
                cost_text = f" ⚪{total_cost}" if total_cost > 0 else ""
                
                # ダメージ表示
                damage_text = f" ({attack_power})" if attack_power > 0 else ""
                
                label = f"⚔️ {attack_name}{damage_text}{cost_text}"
                
                # 制限チェック
                if first_turn_restriction:
                    label += " (先攻1ターン目)"
                    menu.add_command(label=label, state="disabled")
                elif already_attacked:
                    label += " (攻撃済み)"
                    menu.add_command(label=label, state="disabled")
                else:
                    # エネルギーコスト判定
                    from utils.energy_cost_checker import EnergyCostChecker
                    can_use, _ = EnergyCostChecker.can_use_attack(pokemon, 1, self.game_state)
                    
                    if can_use:
                        menu.add_command(
                            label=label,
                            command=lambda: self._on_attack_selected(pokemon, 1)
                        )
                    else:
                        label += " (エネルギー不足)"
                        menu.add_command(label=label, state="disabled")
            
            # ワザ2のチェック
            if hasattr(pokemon, 'attack2_name') and pokemon.attack2_name:
                attacks_found = True
                attack_name = pokemon.attack2_name
                attack_power = getattr(pokemon, 'attack2_power', 0) or 0
                
                # エネルギーコスト表示
                cost_types = getattr(pokemon, 'attack2_cost_types', {}) or {}
                total_cost = sum(cost_types.values()) if cost_types else 0
                cost_text = f" ⚪{total_cost}" if total_cost > 0 else ""
                
                # ダメージ表示
                damage_text = f" ({attack_power})" if attack_power > 0 else ""
                
                label = f"⚔️ {attack_name}{damage_text}{cost_text}"
                
                # 制限チェック
                if first_turn_restriction:
                    label += " (先攻1ターン目)"
                    menu.add_command(label=label, state="disabled")
                elif already_attacked:
                    label += " (攻撃済み)"
                    menu.add_command(label=label, state="disabled")
                else:
                    # エネルギーコスト判定
                    from utils.energy_cost_checker import EnergyCostChecker
                    can_use, _ = EnergyCostChecker.can_use_attack(pokemon, 2, self.game_state)
                    
                    if can_use:
                        menu.add_command(
                            label=label,
                            command=lambda: self._on_attack_selected(pokemon, 2)
                        )
                    else:
                        label += " (エネルギー不足)"
                        menu.add_command(label=label, state="disabled")
            
            return attacks_found
        
        except Exception as e:
            print(f"ワザメニュー追加エラー: {e}")
            return False
        
    def _add_ability_menu(self, menu: Menu, pokemon: Card) -> bool:
        """特性メニューを追加"""
        try:
            if not hasattr(pokemon, 'ability_name') or not pokemon.ability_name:
                return False
            
            # 特性使用可能性チェック（簡単な実装）
            can_use_ability = True  # 後で詳細な判定を実装
            
            if can_use_ability:
                menu.add_command(
                    label=f"✨ {pokemon.ability_name}",
                    command=lambda: self._on_ability_selected(pokemon)
                )
            else:
                menu.add_command(
                    label=f"❌ {pokemon.ability_name} (使用不可)",
                    state="disabled"
                )
            
            return True
        
        except Exception as e:
            print(f"特性メニュー追加エラー: {e}")
            return False
    
    def _add_retreat_menu(self, menu: Menu, pokemon: Card) -> bool:
        """にげるメニューを追加（🆕 v4.31完全実装版）"""
        try:
            # バトル場のポケモンのみにげることができる
            if pokemon != self.game_state.player_active:
                return False
            
            # ベンチにポケモンがいるかチェック
            bench_available = any(p for p in self.game_state.player_bench if p is not None)
            if not bench_available:
                # ベンチにポケモンがいない場合は無効化して表示
                menu.add_command(
                    label="🏃 にげる (ベンチにポケモンがいません)",
                    state="disabled"
                )
                return True
            
            # 特殊状態による制限チェック
            try:
                from utils.special_condition_helper import SpecialConditionHelper
                can_retreat, reason = SpecialConditionHelper.can_retreat(pokemon)
            except ImportError:
                # ヘルパーが見つからない場合はデフォルトで許可
                can_retreat, reason = True, ""
                print("警告: SpecialConditionHelperが見つかりません。特殊状態チェックをスキップします。")
            
            # にげるコストを表示
            retreat_cost = getattr(pokemon, 'retreat_cost', 0) or 0
            
            if can_retreat:
                if retreat_cost == 0:
                    label = "🏃 にげる (コスト: なし)"
                else:
                    # 現在のエネルギー数と比較
                    attached_count = len(getattr(pokemon, 'attached_energy', []))
                    if attached_count >= retreat_cost:
                        label = f"🏃 にげる (コスト: ⚪{retreat_cost})"
                    else:
                        label = f"❌ にげる (エネルギー不足: {retreat_cost}必要/{attached_count}装着)"
                        menu.add_command(label=label, state="disabled")
                        return True
                
                menu.add_command(
                    label=label,
                    command=lambda: self._on_retreat_selected(pokemon)
                )
            else:
                # 特殊状態で制限されている場合
                menu.add_command(
                    label=f"❌ にげる ({reason})",
                    state="disabled"
                )
            
            return True
        
        except Exception as e:
            print(f"にげるメニュー追加エラー: {e}")
            return False
    
    def _on_attack_selected(self, pokemon: Card, attack_number: int):
        """ワザ選択時の処理（先攻1ターン目攻撃制限対応・デバッグ強化版）"""
        try:
            print(f"🔍 コンテキストメニューワザ選択: {pokemon.name} の攻撃{attack_number}")
            
            # ダブルチェック：先攻1ターン目攻撃制限
            if self.game_state.is_first_player_first_turn():
                print("❌ 先攻1ターン目のため攻撃が制限されました")
                return
            
            # ワザの存在確認
            if attack_number == 1:
                attack_name = getattr(pokemon, 'attack_name', None)
            elif attack_number == 2:
                attack_name = getattr(pokemon, 'attack2_name', None)
            else:
                print(f"❌ 無効なワザ番号: {attack_number}")
                return
            
            if not attack_name:
                print(f"❌ ワザ{attack_number}が存在しません")
                return
            
            print(f"✅ ワザ存在確認: {attack_name}")
            
            if self.attack_callback:
                print(f"🎯 攻撃コールバック呼び出し: {pokemon.name}, ワザ{attack_number}")
                self.attack_callback(pokemon, attack_number)
            else:
                print("❌ 攻撃コールバックが設定されていません")
        
        except Exception as e:
            print(f"❌ ワザ選択エラー: {e}")
            import traceback
            traceback.print_exc()
            
    def _on_ability_selected(self, pokemon: Card):
        """特性選択時の処理"""
        try:
            print(f"特性選択: {pokemon.name} の {pokemon.ability_name}")
            
            if self.ability_callback:
                self.ability_callback(pokemon)
            else:
                print("特性は未実装です")
        
        except Exception as e:
            print(f"特性選択エラー: {e}")
    
    def _on_retreat_selected(self, pokemon: Card):
        """にげる選択時の処理（🆕 v4.31完全実装版）"""
        try:
            print(f"🏃 にげる選択: {pokemon.name}")
            
            if self.retreat_callback:
                self.retreat_callback(pokemon)
            else:
                print("にげる機能のコールバックが設定されていません")
        
        except Exception as e:
            print(f"にげる選択エラー: {e}")
    
    def _on_details_selected(self, pokemon: Card):
        """カード詳細選択時の処理"""
        try:
            print(f"詳細表示: {pokemon.name}")
            
            # 現在の位置情報をログ出力（デバッグ用）
            if self.current_pokemon_position:
                side, location, index = self.current_pokemon_position
                print(f"位置情報: {side}-{location}-{index}")
            
            if self.details_callback:
                self.details_callback(pokemon)
            else:
                print("詳細表示コールバックが設定されていません")
        
        except Exception as e:
            print(f"詳細選択エラー: {e}")
    
    def hide_menu(self):
        """メニューを非表示にする"""
        try:
            if self.current_menu:
                self.current_menu.destroy()
                self.current_menu = None
        except Exception as e:
            print(f"メニュー非表示エラー: {e}")
    
    def __del__(self):
        """デストラクタ"""
        self.hide_menu()