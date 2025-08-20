# gui/battle_field_ui.py
# Version: 4.24
# Updated: 2025-06-12 13:20
# バトルフィールドUI：ベンチカード詳細表示不具合修正版

import tkinter as tk
from tkinter import Canvas, Button, Label, Frame
from typing import Callable, Optional, Dict, Tuple
from models.game_state import GameState
from models.card import Card, CardType
from gui.pokemon_context_menu import PokemonContextMenu

class BattleFieldUI:
    """バトルフィールドのUI管理クラス（ベンチカード詳細表示不具合修正版）"""
    
    def __init__(self, parent: tk.Widget, game_state: GameState):
        self.parent = parent
        self.game_state = game_state
        self.field_canvas = None
        
        # UI要素への参照
        self.turn_label = None
        self.current_player_label = None
        self.game_status_label = None
        self.end_turn_button = None
        
        # カウンター表示要素
        self.player_deck_count = None
        self.opponent_deck_count = None
        self.player_hand_count = None
        self.opponent_hand_count = None
        self.player_side_count = None
        self.opponent_side_count = None
        self.player_discard_count = None
        self.opponent_discard_count = None
        
        # コールバック関数
        self.on_field_card_click: Optional[Callable] = None
        self.on_deck_click: Optional[Callable] = None
        self.on_discard_click: Optional[Callable] = None
        self.on_side_click: Optional[Callable] = None
        self.on_trash_click: Optional[Callable] = None
        self.on_pokemon_attack: Optional[Callable[[Card, int], None]] = None
        
        # 🆕 ポケモン位置情報管理（v4.24追加）
        self.pokemon_positions: Dict[int, Tuple[str, str, Optional[int]]] = {}  # pokemon_id -> (side, location, index)
        
        # 統一コンテキストメニューシステム
        self.context_menu = None
    
    def set_callbacks(self,
                     on_field_card_click: Optional[Callable] = None,
                     on_deck_click: Optional[Callable] = None,
                     on_discard_click: Optional[Callable] = None,
                     on_side_click: Optional[Callable] = None,
                     on_trash_click: Optional[Callable] = None,
                     on_pokemon_attack: Optional[Callable[[Card, int], None]] = None,
                     on_end_turn: Optional[Callable] = None):  # 🆕 ターン終了コールバック追加
        """コールバック関数を設定"""
        self.on_field_card_click = on_field_card_click
        self.on_deck_click = on_deck_click
        self.on_discard_click = on_discard_click
        self.on_side_click = on_side_click
        self.on_trash_click = on_trash_click
        self.on_pokemon_attack = on_pokemon_attack
        self.on_end_turn = on_end_turn  # 🆕 ターン終了コールバック保存
        
    def create_battle_field(self):
        """バトルフィールドUIを作成"""
        # ゲーム情報ヘッダー
        self._create_header()
        
        # メインバトルフィールド
        self._create_main_field()
        
        # 統一コンテキストメニューシステムのセットアップ（修正版）
        if self.field_canvas:
            self.context_menu = PokemonContextMenu(self.field_canvas, self.game_state)
            self.context_menu.set_callbacks(
                attack_callback=self._on_attack_selected,
                ability_callback=self._on_ability_selected,
                retreat_callback=self._on_retreat_selected,
                details_callback=self._on_details_selected  # 🆕 修正版コールバック
            )
        
        return self.field_canvas
    
    def _create_header(self):
        """ヘッダー部分を作成"""
        header_frame = Frame(self.parent, bg="lightgreen", height=60)
        header_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        # 左側: ターン情報とプレイヤー情報を統合
        info_left = Frame(header_frame, bg="lightgreen")
        info_left.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.turn_label = Label(info_left, text="ターン: 0", font=("Arial", 12, "bold"), bg="lightgreen")
        self.turn_label.pack(anchor="w")
        
        # プレイヤー情報に先攻/後攻情報を統合
        self.current_player_label = Label(info_left, text="プレイヤー: -", font=("Arial", 10), bg="lightgreen")
        self.current_player_label.pack(anchor="w")
        
        # 🆕 右側: ターン終了ボタンとゲーム状態
        info_right = Frame(header_frame, bg="lightgreen")
        info_right.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        # ターン終了ボタンを右上に配置
        self.end_turn_button = tk.Button(
            info_right,
            text="ターン終了",
            command=self._on_end_turn_clicked,
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=1
        )
        self.end_turn_button.pack(anchor="e", pady=(2, 0))
        
        self.game_status_label = Label(info_right, text="ゲーム準備中", font=("Arial", 10, "bold"), bg="lightgreen")
        self.game_status_label.pack(anchor="e")
        
        # 先攻1ターン目表示エリア
        self.first_turn_label = Label(info_right, text="", font=("Arial", 9), bg="lightgreen", fg="red")
        self.first_turn_label.pack(anchor="e")

    def _on_end_turn_clicked(self):
        """🆕 ターン終了ボタンクリック時の処理"""
        try:
            if self.on_end_turn:
                self.on_end_turn()
            else:
                print("ターン終了コールバックが設定されていません")
        except Exception as e:
            print(f"ターン終了ボタンクリック処理エラー: {e}")

    def _create_main_field(self):
        """メインバトルフィールドを作成（バトルログエリア追加版）"""
        # バトルフィールドキャンバス（幅を拡張してバトルログエリアを確保）
        self.field_canvas = Canvas(
            self.parent,
            width=1500,  # 幅を200拡張
            height=600, 
            bg="darkgreen"
        )
        self.field_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self._draw_field()
        return self.field_canvas

    def _draw_field(self):
        """フィールドを描画（スタジアムエリア呼び出し削除版）"""
        if not self.field_canvas:
            return
        
        # キャンバスをクリア
        self.field_canvas.delete("all")
        
        # フィールドサイズ取得
        canvas_width = self.field_canvas.winfo_reqwidth()
        canvas_height = self.field_canvas.winfo_reqheight()
        
        # フィールド背景を設定
        bg_color = "darkgreen"
        self.field_canvas.configure(bg=bg_color)
        
        # ポケモン描画
        self._draw_opponent_pokemon()
        self._draw_player_pokemon()
        
        # その他の要素（デッキ、捨て札、サイドなど）
        self._draw_other_elements()

    def _draw_stadium_card(self, stadium_x: int, stadium_y: int, stadium_width: int, stadium_height: int):
        """🆕 スタジアムカードを描画（簡素化版）"""
        try:
            # 現在のスタジアムカードを取得
            stadium_card = getattr(self.game_state, 'stadium', None)
            
            if stadium_card:
                # スタジアムカードがある場合
                card_rect = self.field_canvas.create_rectangle(
                    stadium_x, stadium_y, stadium_x + stadium_width, stadium_y + stadium_height,
                    fill="#ffffe0", outline="#ffd700", width=2,
                    tags="stadium_card"
                )
                
                # カード名を表示
                card_name = getattr(stadium_card, 'name', '不明なスタジアム')
                self.field_canvas.create_text(
                    stadium_x + stadium_width // 2, stadium_y + stadium_height // 2,
                    text=card_name, fill="black", font=("Arial", 8, "bold"),
                    tags="stadium_card_name"
                )
                
                # クリック可能にする
                self.field_canvas.tag_bind("stadium_card", "<Button-1>", 
                                        lambda e: self._on_stadium_clicked())
                self.field_canvas.tag_bind("stadium_card_name", "<Button-1>", 
                                        lambda e: self._on_stadium_clicked())
            else:
                # スタジアムカードがない場合
                empty_rect = self.field_canvas.create_rectangle(
                    stadium_x, stadium_y, stadium_x + stadium_width, stadium_y + stadium_height,
                    fill="#2d2d2d", outline="#666666", width=1,
                    tags="stadium_empty"
                )
                
                self.field_canvas.create_text(
                    stadium_x + stadium_width // 2, stadium_y + stadium_height // 2,
                    text="スタジアム", fill="#cccccc", font=("Arial", 8),
                    tags="stadium_empty_text"
                )
        
        except Exception as e:
            print(f"スタジアムカード描画エラー: {e}")

    def _on_stadium_clicked(self):
        """🆕 スタジアムクリック時の処理"""
        try:
            stadium_card = getattr(self.game_state, 'stadium', None)
            
            if stadium_card:
                # スタジアムカードの詳細を表示
                card_info = f"スタジアム: {stadium_card.name}"
                if hasattr(stadium_card, 'ability_description') and stadium_card.ability_description:
                    card_info += f"\n効果: {stadium_card.ability_description}"
                else:
                    card_info += "\n効果: 未実装"
                
                if hasattr(self, 'on_stadium_click') and self.on_stadium_click:
                    self.on_stadium_click(stadium_card)
                else:
                    # デフォルトメッセージ表示
                    print(card_info)
            else:
                print("現在スタジアムは出ていません")
        
        except Exception as e:
            print(f"スタジアムクリック処理エラー: {e}")
    
    def set_stadium_click_callback(self, callback):
        """🆕 スタジアムクリックコールバックを設定"""
        self.on_stadium_click = callback
    
    def _draw_player_pokemon(self):
        """プレイヤーのポケモンを描画（ベンチ間隔調整版）"""
        try:
            # バトル場
            if self.game_state.player_active:
                self._draw_pokemon_card(
                    self.game_state.player_active, 
                    550, 400,  # x座標を左に移動
                    "player_active",
                    owner="player",
                    side="player",
                    location="active",
                    index=None
                )
            
            # ベンチ（間隔を狭める）
            bench_x_start = 150
            bench_spacing = 110  # 150→120に縮小
            bench_y = 550
            
            for i, pokemon in enumerate(self.game_state.player_bench):
                if pokemon:
                    x = bench_x_start + i * bench_spacing
                    self._draw_pokemon_card(
                        pokemon, 
                        x, bench_y, 
                        f"player_bench_{i}",
                        owner="player",
                        side="player",
                        location="bench",
                        index=i
                    )
        
        except Exception as e:
            print(f"プレイヤーポケモン描画エラー: {e}")


    def _draw_opponent_pokemon(self):
        """相手のポケモンを描画（ベンチ間隔調整版）"""
        try:
            # バトル場
            if self.game_state.opponent_active:
                self._draw_pokemon_card(
                    self.game_state.opponent_active, 
                    550, 250,  # x座標を左に移動
                    "opponent_active",
                    owner="opponent",
                    side="opponent",
                    location="active",
                    index=None
                )
            
            # ベンチ（間隔を狭める）
            bench_x_start = 150
            bench_spacing = 110  # 150→120に縮小
            bench_y = 80
            
            for i, pokemon in enumerate(self.game_state.opponent_bench):
                if pokemon:
                    x = bench_x_start + i * bench_spacing
                    self._draw_pokemon_card(
                        pokemon, 
                        x, bench_y, 
                        f"opponent_bench_{i}",
                        owner="opponent",
                        side="opponent",
                        location="bench",
                        index=i
                    )
        
        except Exception as e:
            print(f"相手ポケモン描画エラー: {e}")


    def _draw_pokemon_card(self, pokemon: Card, x: int, y: int, card_id: str, 
                          owner: str = "player", side: str = "player", 
                          location: str = "active", index: Optional[int] = None):
        """ポケモンカードを描画（v4.24修正版：位置情報保持）"""
        try:
            # カードサイズ
            card_width = 90
            card_height = 120
            
            # カード背景
            color = "lightcyan" if owner == "player" else "lightcoral"
            
            self.field_canvas.create_rectangle(
                x - card_width//2, y - card_height//2,
                x + card_width//2, y + card_height//2,
                fill=color, outline="black", width=2,
                tags=card_id
            )
            
            # ポケモン名
            self.field_canvas.create_text(
                x, y - 50, text=pokemon.name,
                font=("Arial", 10, "bold"),
                tags=card_id
            )
            
            # HP表示
            current_hp = pokemon.hp - getattr(pokemon, 'damage_taken', 0)
            hp_text = f"HP: {current_hp}/{pokemon.hp}"
            self.field_canvas.create_text(
                x, y - 30, text=hp_text,
                font=("Arial", 8),
                tags=card_id
            )
            
            # ダメージカウンター（もしあれば）
            damage = getattr(pokemon, 'damage_taken', 0)
            if damage > 0:
                self.field_canvas.create_text(
                    x, y + 40, text=f"ダメージ: {damage}",
                    font=("Arial", 8), fill="red",
                    tags=card_id
                )
            
            # 装着エネルギー数
            energy_count = len(getattr(pokemon, 'attached_energy', []))
            if energy_count > 0:
                self.field_canvas.create_text(
                    x, y + 20, text=f"⚡{energy_count}",
                    font=("Arial", 10),
                    tags=card_id
                )
            
            # 🆕 ポケモン位置情報を保存（v4.24追加）
            pokemon_id = id(pokemon)
            self.pokemon_positions[pokemon_id] = (side, location, index)
            
            # プレイヤーのポケモンのみクリックイベントを設定
            if owner == "player":
                self.field_canvas.tag_bind(card_id, "<Button-1>", 
                                         lambda event, p=pokemon, s=side, l=location, i=index: 
                                         self._on_pokemon_clicked(event, p, s, l, i))
                self.field_canvas.tag_bind(card_id, "<Button-3>", 
                                         lambda event, p=pokemon, s=side, l=location, i=index: 
                                         self._on_pokemon_right_clicked(event, p, s, l, i))
        
        except Exception as e:
            print(f"ポケモンカード描画エラー: {e}")

    def _draw_other_elements(self):
        """その他の要素（デッキ、捨て札など）を描画（スタジアム・手札枚数統合版）"""
        try:
            # 左側一列の基本設定
            left_x = 10  # 50→10に変更
            element_width = 70
            element_height = 50
            spacing = 60
            
            # 相手側（上から）
            start_y = 50
            
            # 1. 相手のデッキ
            opponent_deck_count = len(self.game_state.opponent_deck)
            self.field_canvas.create_rectangle(left_x, start_y, left_x + element_width, start_y + element_height, 
                                            fill="red", outline="black", tags="deck_info")
            self.field_canvas.create_text(left_x + element_width // 2, start_y + element_height // 2, 
                                        text=f"デッキ\n{opponent_deck_count}枚", 
                                        font=("Arial", 8), fill="white", tags="deck_info")
            
            # 2. 相手のサイド
            opponent_side_count = len(self.game_state.opponent_prizes)
            self.field_canvas.create_rectangle(left_x, start_y + spacing, left_x + element_width, start_y + spacing + element_height, 
                                            fill="orange", outline="black", tags="side_info")
            self.field_canvas.create_text(left_x + element_width // 2, start_y + spacing + element_height // 2, 
                                        text=f"サイド\n{opponent_side_count}枚", 
                                        font=("Arial", 8), tags="side_info")
            
            # 3. 相手のトラッシュ
            opponent_discard_count = len(self.game_state.opponent_discard)
            self.field_canvas.create_rectangle(left_x, start_y + spacing * 2, left_x + element_width, start_y + spacing * 2 + element_height, 
                                            fill="darkgray", outline="black", tags="discard_info")
            self.field_canvas.create_text(left_x + element_width // 2, start_y + spacing * 2 + element_height // 2, 
                                        text=f"トラッシュ\n{opponent_discard_count}枚", 
                                        font=("Arial", 8), tags="discard_info")
            
            # 4. 相手手札枚数（新規追加）
            opponent_hand_count = len(self.game_state.opponent_hand)
            self.field_canvas.create_rectangle(left_x, start_y + spacing * 3, left_x + element_width, start_y + spacing * 3 + element_height, 
                                            fill="lightpink", outline="black", tags="hand_info")
            self.field_canvas.create_text(left_x + element_width // 2, start_y + spacing * 3 + element_height // 2, 
                                        text=f"手札\n{opponent_hand_count}枚", 
                                        font=("Arial", 8), tags="hand_info")
            
            # 5. スタジアム
            stadium_y = start_y + spacing * 4
            stadium_card = getattr(self.game_state, 'stadium', None)
            
            if stadium_card:
                # スタジアムカードがある場合
                self.field_canvas.create_rectangle(left_x, stadium_y, left_x + element_width, stadium_y + element_height,
                                                fill="#ffffe0", outline="#ffd700", width=2, tags="stadium_card")
                
                # カード名を表示
                card_name = getattr(stadium_card, 'name', '不明なスタジアム')
                self.field_canvas.create_text(left_x + element_width // 2, stadium_y + element_height // 2,
                                            text=card_name, fill="black", font=("Arial", 8, "bold"), tags="stadium_card_name")
                
                # クリック可能にする
                self.field_canvas.tag_bind("stadium_card", "<Button-1>", lambda e: self._on_stadium_clicked())
                self.field_canvas.tag_bind("stadium_card_name", "<Button-1>", lambda e: self._on_stadium_clicked())
            else:
                # スタジアムカードがない場合
                self.field_canvas.create_rectangle(left_x, stadium_y, left_x + element_width, stadium_y + element_height,
                                                fill="#2d2d2d", outline="#666666", width=1, tags="stadium_empty")
                
                self.field_canvas.create_text(left_x + element_width // 2, stadium_y + element_height // 2,
                                            text="スタジアム", fill="#cccccc", font=("Arial", 8), tags="stadium_empty_text")
            
            # プレイヤー側（下から）
            bottom_y = 520
            
            # 6. プレイヤーのデッキ
            player_deck_count = len(self.game_state.player_deck)
            self.field_canvas.create_rectangle(left_x, bottom_y - element_height, left_x + element_width, bottom_y, 
                                            fill="blue", outline="black", tags="deck_info")
            self.field_canvas.create_text(left_x + element_width // 2, bottom_y - element_height // 2, 
                                        text=f"デッキ\n{player_deck_count}枚", 
                                        font=("Arial", 8), fill="white", tags="deck_info")
            
            # 7. プレイヤーのサイド
            player_side_count = len(self.game_state.player_prizes)
            self.field_canvas.create_rectangle(left_x, bottom_y - spacing - element_height, left_x + element_width, bottom_y - spacing, 
                                            fill="gold", outline="black", tags="side_info")
            self.field_canvas.create_text(left_x + element_width // 2, bottom_y - spacing - element_height // 2, 
                                        text=f"サイド\n{player_side_count}枚", 
                                        font=("Arial", 8), tags="side_info")
            
            # 8. プレイヤーのトラッシュ
            player_discard_count = len(self.game_state.player_discard)
            self.field_canvas.create_rectangle(left_x, bottom_y - spacing * 2 - element_height, left_x + element_width, bottom_y - spacing * 2, 
                                            fill="gray", outline="black", tags="discard_info")
            self.field_canvas.create_text(left_x + element_width // 2, bottom_y - spacing * 2 - element_height // 2, 
                                        text=f"トラッシュ\n{player_discard_count}枚", 
                                        font=("Arial", 8), tags="discard_info")
            
            # バトルログエリアを描画
            self._draw_battle_log_area()
        
        except Exception as e:
            print(f"その他要素描画エラー: {e}")

    def _draw_battle_log_area(self):
        """バトルログエリアを描画"""
        try:
            # バトルログエリアの位置とサイズ
            log_x = 1050
            log_y = 50
            log_width = 300
            log_height = 500
            
            # バトルログフレーム
            self.field_canvas.create_rectangle(
                log_x, log_y, log_x + log_width, log_y + log_height,
                fill="white", outline="black", width=2,
                tags="battle_log_frame"
            )
            
            # バトルログタイトル
            self.field_canvas.create_text(
                log_x + log_width // 2, log_y + 20,
                text="📋 バトルログ", fill="black", font=("Arial", 12, "bold"),
                tags="battle_log_title"
            )
            
            # ログ表示エリア（背景）
            log_area_x = log_x + 10
            log_area_y = log_y + 40
            log_area_width = log_width - 20
            log_area_height = log_height - 50
            
            self.field_canvas.create_rectangle(
                log_area_x, log_area_y, 
                log_area_x + log_area_width, log_area_y + log_area_height,
                fill="#f8f8f8", outline="gray", width=1,
                tags="battle_log_area"
            )
            
            # プレースホルダーテキスト
            placeholder_texts = [
                "ゲーム開始",
                "プレイヤーのターン開始",
                "カードをドローしました",
                "",
                "（バトルログがここに表示されます）"
            ]
            
            for i, text in enumerate(placeholder_texts):
                if text:  # 空文字でない場合のみ表示
                    self.field_canvas.create_text(
                        log_area_x + 10, log_area_y + 20 + i * 20,
                        text=text, fill="gray", font=("Arial", 9),
                        anchor="w", tags="battle_log_placeholder"
                    )
            
            print("バトルログエリア描画完了")
            
        except Exception as e:
            print(f"バトルログエリア描画エラー: {e}")


    def _on_pokemon_clicked(self, event, pokemon: Card, side: str, location: str, index: Optional[int]):
        """ポケモンの左クリック処理（v4.24修正版：位置情報付き）"""
        try:
            print(f"ポケモンクリック: {pokemon.name} at {side}-{location}-{index}")
            
            if self.context_menu:
                # 🆕 位置情報を保持してコンテキストメニューに渡す
                self.context_menu.current_pokemon_position = (side, location, index)
                self.context_menu.show_pokemon_menu(event, pokemon, side)
        
        except Exception as e:
            print(f"ポケモンクリック処理エラー: {e}")
    
    def _on_pokemon_right_clicked(self, event, pokemon: Card, side: str, location: str, index: Optional[int]):
        """ポケモンの右クリック処理（v4.24修正版：位置情報付き）"""
        try:
            print(f"ポケモン右クリック: {pokemon.name} at {side}-{location}-{index}")
            
            if self.context_menu:
                # 🆕 位置情報を保持してコンテキストメニューに渡す
                self.context_menu.current_pokemon_position = (side, location, index)
                self.context_menu.show_pokemon_menu(event, pokemon, side)
        
        except Exception as e:
            print(f"ポケモン右クリック処理エラー: {e}")
    
    def _on_attack_selected(self, pokemon: Card, attack_number: int):
        """ワザ選択時のコールバック"""
        try:
            print(f"ワザ選択: {pokemon.name} の攻撃{attack_number}")
            
            if self.on_pokemon_attack:
                self.on_pokemon_attack(pokemon, attack_number)
            else:
                print("攻撃コールバックが設定されていません")
        
        except Exception as e:
            print(f"ワザ選択コールバックエラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_ability_selected(self, pokemon: Card):
        """特性選択時のコールバック"""
        try:
            print(f"特性使用: {pokemon.name} の {pokemon.ability_name}")
            from tkinter import messagebox
            messagebox.showinfo("特性", f"{pokemon.ability_name}\n\n特性システムは未実装です。")
        
        except Exception as e:
            print(f"特性選択エラー: {e}")
    
    def _on_retreat_selected(self, pokemon: Card):
        """にげる選択時のコールバック"""
        try:
            print(f"にげる実行: {pokemon.name}")
            from tkinter import messagebox
            messagebox.showinfo("にげる", f"{pokemon.name}のにげる\n\nにげるシステムは未実装です。")
        
        except Exception as e:
            print(f"にげる選択エラー: {e}")
    
    def _on_details_selected(self, pokemon: Card):
        """カード詳細選択時のコールバック（v4.24修正版）"""
        try:
            print(f"詳細表示: {pokemon.name}")
            
            # 🆕 修正：コンテキストメニューから正しい位置情報を取得
            if hasattr(self.context_menu, 'current_pokemon_position') and self.context_menu.current_pokemon_position:
                side, location, index = self.context_menu.current_pokemon_position
                print(f"位置情報: {side}-{location}-{index}")
            else:
                # フォールバック：ポケモンオブジェクトから位置を特定
                side, location, index = self._find_pokemon_position(pokemon)
                print(f"位置情報（検索結果）: {side}-{location}-{index}")
            
            if self.on_field_card_click:
                self.on_field_card_click(side, location, index, "show_details")
            else:
                # デフォルトの詳細表示
                self._show_default_pokemon_details(pokemon)
        
        except Exception as e:
            print(f"詳細表示エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _find_pokemon_position(self, pokemon: Card) -> Tuple[str, str, Optional[int]]:
        """ポケモンオブジェクトから位置を特定（v4.24新規）"""
        try:
            # プレイヤーバトル場をチェック
            if self.game_state.player_active == pokemon:
                return ("player", "active", None)
            
            # プレイヤーベンチをチェック
            for i, bench_pokemon in enumerate(self.game_state.player_bench):
                if bench_pokemon == pokemon:
                    return ("player", "bench", i)
            
            # 相手バトル場をチェック
            if self.game_state.opponent_active == pokemon:
                return ("opponent", "active", None)
            
            # 相手ベンチをチェック
            for i, bench_pokemon in enumerate(self.game_state.opponent_bench):
                if bench_pokemon == pokemon:
                    return ("opponent", "bench", i)
            
            # 見つからない場合はデフォルト
            print(f"警告: {pokemon.name}の位置が特定できませんでした")
            return ("player", "active", None)
        
        except Exception as e:
            print(f"ポケモン位置特定エラー: {e}")
            return ("player", "active", None)
    
    def _show_default_pokemon_details(self, pokemon: Card):
        """デフォルトのポケモン詳細表示（v4.24新規）"""
        try:
            from tkinter import messagebox
            
            details = f"名前: {pokemon.name}\n"
            details += f"タイプ: {getattr(pokemon, 'pokemon_type', '不明')}\n"
            
            if pokemon.hp:
                current_hp = pokemon.hp - getattr(pokemon, 'damage_taken', 0)
                details += f"HP: {current_hp}/{pokemon.hp}\n"
            
            if pokemon.attack_name:
                details += f"\nワザ1: {pokemon.attack_name}"
                if pokemon.attack_power:
                    details += f" ({pokemon.attack_power}ダメージ)"
            
            if hasattr(pokemon, 'attack2_name') and pokemon.attack2_name:
                details += f"\nワザ2: {pokemon.attack2_name}"
                if hasattr(pokemon, 'attack2_power') and pokemon.attack2_power:
                    details += f" ({pokemon.attack2_power}ダメージ)"
            
            if hasattr(pokemon, 'ability_name') and pokemon.ability_name:
                details += f"\n特性: {pokemon.ability_name}"
            
            messagebox.showinfo(f"{pokemon.name} の詳細", details)
        
        except Exception as e:
            print(f"デフォルト詳細表示エラー: {e}")

    def _update_turn_display(self):
        """ターン表示を更新"""
        try:
            if self.turn_label:
                self.turn_label.config(text=f"ターン: {self.game_state.turn_count}")
            
            if self.current_player_label:
                # 🆕 プレイヤー情報に先攻/後攻情報を統合
                current_player_text = "あなた" if self.game_state.current_player == "player" else "相手"
                
                # 先攻/後攻情報を追加
                first_player_info = ""
                if hasattr(self.game_state, 'first_player') and self.game_state.first_player:
                    if self.game_state.current_player == "player":
                        if self.game_state.first_player == "player":
                            first_player_info = "（先攻）"
                        else:
                            first_player_info = "（後攻）"
                    else:
                        if self.game_state.first_player == "opponent":
                            first_player_info = "（先攻）"
                        else:
                            first_player_info = "（後攻）"
                
                player_text = f"プレイヤー: {current_player_text}{first_player_info}"
                self.current_player_label.config(text=player_text)
            
            if self.game_status_label:
                if hasattr(self.game_state, 'initialization_complete') and self.game_state.initialization_complete:
                    if self.game_state.current_player == "player":
                        status_text = "あなたのターンです"
                    else:
                        status_text = "相手のターンです"
                else:
                    status_text = "ゲーム準備中"
                self.game_status_label.config(text=status_text)
            
            # 先攻1ターン目の警告表示
            if self.first_turn_label:
                if self.game_state.is_first_player_first_turn():
                    warning_text = "先攻1ターン目（攻撃・サポート不可）"
                    self.first_turn_label.config(text=warning_text)
                else:
                    self.first_turn_label.config(text="")
        
        except Exception as e:
            print(f"ターン表示更新エラー: {e}")
    
    def _update_pokemon_display(self):
        """ポケモン表示を更新"""
        try:
            # 既存のポケモン表示をクリア
            self.field_canvas.delete("player_active", "opponent_active")
            for i in range(5):
                self.field_canvas.delete(f"player_bench_{i}")
                self.field_canvas.delete(f"opponent_bench_{i}")
            
            # ポケモンを再描画
            self._draw_player_pokemon()
            self._draw_opponent_pokemon()
        
        except Exception as e:
            print(f"ポケモン表示更新エラー: {e}")

    def _update_left_panel_display(self):
        """左側パネル表示を更新（デッキ・サイド・トラッシュ・手札・スタジアム統合版）"""
        try:
            # 既存の左側パネル表示をクリア
            self.field_canvas.delete("deck_info", "discard_info", "side_info", "hand_info", 
                                "stadium_card", "stadium_card_name", "stadium_empty", "stadium_empty_text")
            
            # 左側パネル要素を再描画
            self._draw_other_elements()
            
        except Exception as e:
            print(f"左側パネル表示更新エラー: {e}")

    def update_display(self):
        """表示を更新（左側パネル統合版）"""
        try:
            # 既存の更新処理
            self._update_turn_display()
            self._update_pokemon_display()
            self._update_left_panel_display()  # 統合されたメソッドを呼び出し
            
        except Exception as e:
            print(f"表示更新エラー: {e}")
