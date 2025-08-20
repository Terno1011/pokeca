# gui/attack_selection_dialog.py
# Version: 4.23
# Updated: 2025-06-11 18:55
# 先攻1ターン目攻撃制限対応・tkinter Menu インポートエラー修正版

import tkinter as tk
from tkinter import Toplevel, Label, Button, Frame, messagebox, Menu
from typing import Callable, Optional, List, Tuple
from models.card import Card
from utils.energy_cost_checker import EnergyCostChecker

class AttackSelectionDialog:
    """ワザ選択ダイアログクラス（先攻1ターン目攻撃制限対応）"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
    
    def show_attack_selection(self, pokemon: Card, 
                             callback: Callable[[Optional[int]], None],
                             game_state=None):
        """
        ワザ選択ダイアログを表示（先攻1ターン目攻撃制限対応）
        
        Args:
            pokemon: 攻撃するポケモン
            callback: 選択結果のコールバック（ワザ番号 or None）
            game_state: ゲーム状態（先攻1ターン目チェック用）
        """
        # 🆕 先攻1ターン目の攻撃制限チェック（v4.23追加）
        if game_state and hasattr(game_state, 'is_first_player_first_turn'):
            if game_state.is_first_player_first_turn():
                messagebox.showwarning(
                    "攻撃制限", 
                    "先攻プレイヤーの最初のターンは攻撃できません。"
                )
                callback(None)
                return
        
        # 使用可能なワザを取得（ゲーム状態を渡して先攻1ターン目チェック含む）
        available_attacks = EnergyCostChecker.get_available_attacks(pokemon, game_state)
        
        if not available_attacks:
            messagebox.showinfo("ワザなし", f"{pokemon.name}にはワザが設定されていません。")
            callback(None)
            return
        
        # すべてのワザが使用不可能かチェック
        usable_attacks = [attack for attack in available_attacks if attack[2]]  # attack[2] is can_use
        
        if not usable_attacks:
            # 先攻1ターン目制限のメッセージを優先表示
            if game_state and hasattr(game_state, 'is_first_player_first_turn'):
                if game_state.is_first_player_first_turn():
                    messagebox.showinfo(
                        "攻撃制限", 
                        f"{pokemon.name}のワザは現在使用できません。\n\n理由：先攻プレイヤーの最初のターンは攻撃できません。"
                    )
                else:
                    messagebox.showinfo(
                        "エネルギー不足", 
                        f"{pokemon.name}のワザは現在使用できません。\n\n理由：エネルギーが不足しています。"
                    )
            else:
                messagebox.showinfo(
                    "ワザ使用不可", 
                    f"{pokemon.name}のワザは現在使用できません。"
                )
            callback(None)
            return
        
        # ダイアログ作成
        dialog_width = min(700, int(self.screen_width * 0.45))
        dialog_height = min(500, int(self.screen_height * 0.6))
        
        dialog = Toplevel(self.parent)
        dialog.title(f"ワザ選択 - {pokemon.name}")
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # ダイアログ中央配置
        dialog.update_idletasks()
        x = max(25, (self.screen_width // 2) - (dialog_width // 2))
        y = max(25, (self.screen_height // 2) - (dialog_height // 2))
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # ヘッダー
        self._create_header(dialog, pokemon, game_state)
        
        # ワザ選択エリア
        self._create_attack_selection_area(dialog, available_attacks, callback)
        
        # エネルギー状況表示
        self._create_energy_status_area(dialog, pokemon)
        
        # ボタンエリア
        self._create_button_area(dialog, callback)
    
    def _create_header(self, dialog: Toplevel, pokemon: Card, game_state=None):
        """ヘッダー部分を作成（先攻1ターン目表示対応）"""
        header_frame = Frame(dialog, bg="#ffe6e6", relief="raised", bd=2, height=80)
        header_frame.pack(fill="x", padx=10, pady=8)
        header_frame.pack_propagate(False)
        
        Label(header_frame, text="⚔️ ワザ選択", 
              font=("Arial", 16, "bold"), bg="#ffe6e6").pack(pady=5)
        
        # ポケモン情報
        pokemon_info = f"{pokemon.name}"
        if pokemon.hp:
            current_hp = pokemon.hp - getattr(pokemon, 'damage_taken', 0)
            pokemon_info += f" (HP: {current_hp}/{pokemon.hp})"
        if hasattr(pokemon, 'pokemon_type') and pokemon.pokemon_type:
            pokemon_info += f" [{pokemon.pokemon_type}]"
        
        Label(header_frame, text=pokemon_info, 
              font=("Arial", 12), bg="#ffe6e6").pack(pady=2)
        
        # 🆕 先攻1ターン目警告表示（v4.23追加）
        if game_state and hasattr(game_state, 'is_first_player_first_turn'):
            if game_state.is_first_player_first_turn():
                Label(header_frame, text="⚠️ 先攻1ターン目：攻撃制限中", 
                      font=("Arial", 10, "bold"), bg="#ffe6e6", fg="red").pack(pady=1)
    
    def _create_attack_selection_area(self, dialog: Toplevel, 
                                    available_attacks: List[Tuple[int, str, bool, str]], 
                                    callback: Callable[[Optional[int]], None]):
        """ワザ選択エリアを作成"""
        selection_frame = Frame(dialog, relief="ridge", bd=2)
        selection_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        Label(selection_frame, text="🎯 使用するワザを選択", 
              font=("Arial", 14, "bold")).pack(pady=8)
        
        # ワザ選択用の変数
        self.attack_selection = tk.IntVar()
        self.attack_selection.set(-1)  # 初期値は未選択
        
        # 各ワザのラジオボタンを作成
        attacks_frame = Frame(selection_frame)
        attacks_frame.pack(fill="both", expand=True, padx=15, pady=8)
        
        for i, (attack_number, attack_name, can_use, details) in enumerate(available_attacks):
            self._create_attack_option(attacks_frame, attack_number, attack_name, 
                                     can_use, details, i)
        
        # 選択を保存（コールバック用）
        self.available_attacks = available_attacks
        self.selection_callback = callback
    
    def _create_attack_option(self, parent: Frame, attack_number: int, 
                            attack_name: str, can_use: bool, details: str, index: int):
        """個別のワザ選択オプションを作成（先攻1ターン目制限対応）"""
        # ワザごとのフレーム
        attack_frame = Frame(parent, relief="groove", bd=2, 
                           bg="lightgreen" if can_use else "lightgray")
        attack_frame.pack(fill="x", padx=5, pady=3)
        
        # ラジオボタン
        state = "normal" if can_use else "disabled"
        radio = tk.Radiobutton(
            attack_frame,
            text=f"ワザ{attack_number}: {attack_name}",
            variable=self.attack_selection,
            value=index,
            state=state,
            font=("Arial", 12, "bold"),
            bg="lightgreen" if can_use else "lightgray"
        )
        radio.pack(anchor="w", padx=10, pady=5)
        
        # 詳細情報
        detail_text = details
        
        # 先攻1ターン目制限の場合は特別なメッセージを表示
        if not can_use and "先攻プレイヤーの最初のターン" in details:
            detail_text = "❌ 先攻1ターン目は攻撃できません"
        elif not can_use:
            detail_text = f"❌ {details}"
        else:
            detail_text = f"✅ {details}"
        
        Label(attack_frame, text=detail_text,
              font=("Arial", 10), 
              bg="lightgreen" if can_use else "lightgray",
              wraplength=600, justify="left").pack(anchor="w", padx=25, pady=2)
    
    def _create_energy_status_area(self, dialog: Toplevel, pokemon: Card):
        """エネルギー状況表示エリアを作成"""
        energy_frame = Frame(dialog, relief="ridge", bd=2)
        energy_frame.pack(fill="x", padx=15, pady=5)
        
        Label(energy_frame, text="⚡ エネルギー状況", 
              font=("Arial", 12, "bold")).pack(pady=5)
        
        # 装着エネルギーの詳細
        energy_summary = EnergyCostChecker.get_energy_status_summary(pokemon)
        Label(energy_frame, text=energy_summary,
              font=("Arial", 10), wraplength=600).pack(pady=2)
    
    def _create_button_area(self, dialog: Toplevel, callback: Callable[[Optional[int]], None]):
        """ボタンエリアを作成"""
        button_frame = Frame(dialog)
        button_frame.pack(fill="x", padx=15, pady=10)
        
        def on_attack():
            """攻撃実行"""
            selection_index = self.attack_selection.get()
            if selection_index == -1:
                messagebox.showwarning("選択エラー", "使用するワザを選択してください。")
                return
            
            # 選択されたワザの情報を取得
            attack_number, attack_name, can_use, details = self.available_attacks[selection_index]
            
            if not can_use:
                # 先攻1ターン目制限の場合は特別なメッセージ
                if "先攻プレイヤーの最初のターン" in details:
                    messagebox.showwarning("攻撃制限", "先攻プレイヤーの最初のターンは攻撃できません。")
                else:
                    messagebox.showwarning("使用不可", f"「{attack_name}」は現在使用できません。")
                return
            
            # 確認ダイアログ
            if messagebox.askyesno("攻撃確認", f"「{attack_name}」を使用しますか？\n\n{details}"):
                dialog.destroy()
                callback(attack_number)
        
        def on_cancel():
            """キャンセル"""
            dialog.destroy()
            callback(None)
        
        def on_energy_check():
            """エネルギー詳細チェック"""
            selection_index = self.attack_selection.get()
            if selection_index == -1:
                messagebox.showinfo("エネルギー詳細", "ワザを選択してください。")
                return
            
            attack_number, attack_name, can_use, details = self.available_attacks[selection_index]
            messagebox.showinfo(f"「{attack_name}」の詳細", details)
        
        # ボタン配置
        Button(button_frame, text="エネルギー詳細", command=on_energy_check,
               font=("Arial", 11), bg="lightblue", width=12, height=2).pack(side="left", padx=5)
        
        Button(button_frame, text="キャンセル", command=on_cancel,
               font=("Arial", 12), width=12, height=2).pack(side="right", padx=5)
        
        Button(button_frame, text="攻撃実行", command=on_attack,
               font=("Arial", 12, "bold"), bg="lightcoral", width=14, height=2).pack(side="right", padx=5)


class AttackMenuManager:
    """攻撃メニュー管理クラス（先攻1ターン目攻撃制限対応・修正版）"""
    
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.attack_dialog = None
    
    def show_pokemon_attack_menu(self, event, pokemon: Card, 
                                attack_callback: Callable[[int], None],
                                game_state=None):
        """ポケモンの攻撃メニューを表示（先攻1ターン目攻撃制限対応・修正版）"""
        try:
            # 修正：正しいMenuのインポートと使用
            context_menu = Menu(self.parent, tearoff=0)
            
            # 🆕 先攻1ターン目攻撃制限チェック（v4.23追加）
            is_first_turn_restriction = False
            if game_state and hasattr(game_state, 'is_first_player_first_turn'):
                is_first_turn_restriction = game_state.is_first_player_first_turn()
            
            # 使用可能なワザを取得（ゲーム状態を渡す）
            available_attacks = EnergyCostChecker.get_available_attacks(pokemon, game_state)
            
            if not available_attacks:
                context_menu.add_command(label="ワザなし", state="disabled")
            else:
                # ワザ選択ダイアログを開くメニュー
                context_menu.add_command(
                    label="🎯 ワザを選択...",
                    command=lambda: self._show_attack_dialog(pokemon, attack_callback, game_state)
                )
                
                context_menu.add_separator()
                
                # 各ワザを直接選択するメニュー
                for attack_number, attack_name, can_use, details in available_attacks:
                    # 先攻1ターン目制限を考慮
                    actual_can_use = can_use and not is_first_turn_restriction
                    
                    if actual_can_use:
                        status_text = "✅"
                        menu_text = f"{status_text} ワザ{attack_number}: {attack_name}"
                        context_menu.add_command(
                            label=menu_text,
                            command=lambda num=attack_number: attack_callback(num)
                        )
                    else:
                        if is_first_turn_restriction:
                            status_text = "⚠️"
                            menu_text = f"{status_text} ワザ{attack_number}: {attack_name} (先攻1ターン目)"
                        else:
                            status_text = "❌"
                            menu_text = f"{status_text} ワザ{attack_number}: {attack_name} (エネルギー不足)"
                        
                        context_menu.add_command(label=menu_text, state="disabled")
            
            # 先攻1ターン目の場合は説明を追加
            if is_first_turn_restriction:
                context_menu.add_separator()
                context_menu.add_command(
                    label="💡 先攻1ターン目は攻撃できません",
                    state="disabled"
                )
            
            context_menu.add_separator()
            
            # その他のメニュー
            context_menu.add_command(
                label="⚡ エネルギー状況確認",
                command=lambda: self._show_energy_status(pokemon)
            )
            
            context_menu.add_command(
                label="📋 ポケモン詳細",
                command=lambda: self._show_pokemon_detail(pokemon)
            )
            
            # メニューを表示
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        
        except Exception as e:
            print(f"攻撃メニュー表示エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_attack_dialog(self, pokemon: Card, 
                           attack_callback: Callable[[int], None],
                           game_state=None):
        """攻撃選択ダイアログを表示（先攻1ターン目攻撃制限対応）"""
        try:
            if self.attack_dialog:
                return  # 既に表示中
            
            self.attack_dialog = AttackSelectionDialog(self.parent)
            
            def dialog_callback(attack_number: Optional[int]):
                self.attack_dialog = None
                if attack_number is not None:
                    attack_callback(attack_number)
            
            # ゲーム状態を渡してダイアログを表示
            self.attack_dialog.show_attack_selection(pokemon, dialog_callback, game_state)
        
        except Exception as e:
            print(f"攻撃ダイアログ表示エラー: {e}")
            self.attack_dialog = None
    
    def _show_energy_status(self, pokemon: Card):
        """エネルギー状況を表示"""
        try:
            energy_status = EnergyCostChecker.get_energy_status_summary(pokemon)
            available_attacks = EnergyCostChecker.get_available_attacks(pokemon)
            
            message = f"【{pokemon.name}のエネルギー状況】\n\n"
            message += f"{energy_status}\n\n"
            message += "【ワザの使用可能性】\n"
            
            if not available_attacks:
                message += "ワザが設定されていません"
            else:
                for attack_number, attack_name, can_use, _ in available_attacks:
                    status = "✅ 使用可能" if can_use else "❌ 使用不可"
                    message += f"ワザ{attack_number}: {attack_name} - {status}\n"
            
            messagebox.showinfo("エネルギー状況", message)
        
        except Exception as e:
            print(f"エネルギー状況表示エラー: {e}")
    
    def _show_pokemon_detail(self, pokemon: Card):
        """ポケモン詳細を表示（簡易版）"""
        try:
            message = f"【{pokemon.name}の詳細】\n\n"
            
            if pokemon.hp:
                current_hp = pokemon.hp - getattr(pokemon, 'damage_taken', 0)
                message += f"HP: {current_hp}/{pokemon.hp}\n"
            
            if hasattr(pokemon, 'pokemon_type') and pokemon.pokemon_type:
                message += f"タイプ: {pokemon.pokemon_type}\n"
            
            if pokemon.weakness:
                message += f"弱点: {pokemon.weakness}\n"
            
            if pokemon.resistance:
                message += f"抵抗力: {pokemon.resistance}\n"
            
            if pokemon.retreat_cost is not None:
                message += f"にげるコスト: {pokemon.retreat_cost}\n"
            
            messagebox.showinfo("ポケモン詳細", message)
        
        except Exception as e:
            print(f"ポケモン詳細表示エラー: {e}")