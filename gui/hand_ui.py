# gui/hand_ui.py
# Version: 4.7
# Updated: 2025-06-10 20:40
# 手札UI管理クラス：メソッド名修正版

import tkinter as tk
from tkinter import Canvas, Frame, Label, Button
from typing import Callable, Optional, List
from models.game_state import GameState
from models.card import Card, CardType

class HandUI:
    """手札UIの管理クラス（メソッド名修正版）"""
    
    def __init__(self, parent: tk.Widget, game_state: GameState):
        self.parent = parent
        self.game_state = game_state
        
        # UI要素
        self.hand_frame = None
        self.hand_canvas = None
        self.hand_info_label = None
        
        # コールバック関数（修正：正しいメソッド名）
        self.hand_card_click_callback: Optional[Callable[[int], None]] = None
        
        # UI状態
        self.interaction_disabled = False
    
    def setup_hand_ui(self):
        """手札UIをセットアップ"""
        try:
            # 手札フレーム
            self.hand_frame = Frame(self.parent, bg="lightblue", height=200)
            self.hand_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
            self.hand_frame.pack_propagate(False)
            
            # 手札情報ヘッダー
            info_frame = Frame(self.hand_frame, bg="lightblue", height=30)
            info_frame.pack(side=tk.TOP, fill=tk.X)
            info_frame.pack_propagate(False)
            
            self.hand_info_label = Label(info_frame, text="手札: 0枚", 
                                       font=("Arial", 12, "bold"), bg="lightblue")
            self.hand_info_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            # 手札カード表示エリア
            canvas_frame = Frame(self.hand_frame, bg="lightblue")
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            self.hand_canvas = Canvas(canvas_frame, bg="white", height=160)
            self.hand_canvas.pack(fill=tk.BOTH, expand=True)
            
            # マウスホイールでスクロール
            self.hand_canvas.bind("<MouseWheel>", self._on_mousewheel)
            
            print("手札UI初期化完了")
            return self.hand_frame
        
        except Exception as e:
            print(f"手札UI作成エラー: {e}")
            return None
    
    def set_callbacks(self, hand_card_click: Callable[[int], None]):
        """コールバック関数を設定（修正版）"""
        self.hand_card_click_callback = hand_card_click
    
    def set_interaction_disabled(self, disabled: bool):
        """手札の操作を無効化/有効化"""
        self.interaction_disabled = disabled
        self.update_display()
    
    def update_display(self):
        """手札表示の更新"""
        try:
            if not self.hand_canvas:
                return
            
            # 既存の表示をクリア
            self.hand_canvas.delete("all")
            
            hand_cards = getattr(self.game_state, 'player_hand', [])
            
            # 手札情報の更新
            self._update_hand_info(hand_cards)
            
            if not hand_cards:
                # 手札が空の場合
                self.hand_canvas.create_text(
                    100, 85, 
                    text="手札が空です", 
                    fill="gray", 
                    font=("Arial", 12)
                )
                return
            
            # カードを横並びで表示
            card_width = 120
            card_height = 160
            card_spacing = 130
            start_x = 10
            
            for i, card in enumerate(hand_cards):
                x = start_x + i * card_spacing
                y = 5
                
                # 操作無効化時の視覚効果
                if self.interaction_disabled:
                    card_color = self._get_disabled_card_color(card)
                    text_color = "darkgray"
                else:
                    card_color = self._get_card_color(card)
                    text_color = "black"
                
                # カードの背景
                card_rect = self.hand_canvas.create_rectangle(
                    x, y, x + card_width, y + card_height,
                    fill=card_color,
                    outline="black" if not self.interaction_disabled else "gray",
                    width=2,
                    tags=f"card_{i}"
                )
                
                # 操作無効化時のオーバーレイ
                if self.interaction_disabled:
                    self.hand_canvas.create_rectangle(
                        x, y, x + card_width, y + card_height,
                        fill="gray",
                        stipple="gray50",
                        tags=f"card_{i}_overlay"
                    )
                
                # カード名
                name_text = card.name
                if len(name_text) > 12:
                    name_text = name_text[:12] + "..."
                
                self.hand_canvas.create_text(
                    x + card_width // 2, y + 15,
                    text=name_text,
                    fill=text_color,
                    font=("Arial", 10, "bold"),
                    tags=f"card_{i}"
                )
                
                # カードタイプ
                self.hand_canvas.create_text(
                    x + card_width // 2, y + 35,
                    text=card.card_type.value,
                    fill=text_color,
                    font=("Arial", 8),
                    tags=f"card_{i}"
                )
                
                # カード固有情報
                if card.card_type == CardType.POKEMON:
                    # ポケモンの場合：HP
                    if card.hp:
                        self.hand_canvas.create_text(
                            x + card_width // 2, y + 55,
                            text=f"HP: {card.hp}",
                            fill=text_color,
                            font=("Arial", 9),
                            tags=f"card_{i}"
                        )
                    
                    # ポケモンタイプ
                    if card.pokemon_type:
                        self.hand_canvas.create_text(
                            x + card_width // 2, y + 75,
                            text=card.pokemon_type,
                            fill=text_color,
                            font=("Arial", 9),
                            tags=f"card_{i}"
                        )
                    
                    # 進化情報
                    if hasattr(card, 'evolve_step') and card.evolve_step > 0:
                        evolve_text = f"進化Lv.{card.evolve_step}"
                        if card.evolves_from:
                            evolve_text += f" ← {card.evolves_from}"
                        self.hand_canvas.create_text(
                            x + card_width // 2, y + 95,
                            text=evolve_text,
                            fill=text_color,
                            font=("Arial", 7),
                            tags=f"card_{i}"
                        )
                    
                    # 攻撃情報
                    if card.attack_name:
                        attack_text = card.attack_name
                        if card.attack_power:
                            attack_text += f" ({card.attack_power})"
                        self.hand_canvas.create_text(
                            x + card_width // 2, y + 115,
                            text=attack_text,
                            fill=text_color,
                            font=("Arial", 8),
                            tags=f"card_{i}"
                        )
                
                elif card.card_type == CardType.TRAINER:
                    # トレーナーの場合：サブタイプ
                    if hasattr(card, 'trainer_type') and card.trainer_type:
                        self.hand_canvas.create_text(
                            x + card_width // 2, y + 55,
                            text=card.trainer_type.value.upper(),
                            fill=text_color,
                            font=("Arial", 9, "bold"),
                            tags=f"card_{i}"
                        )
                
                elif card.card_type == CardType.ENERGY:
                    # エネルギーの場合：種類
                    if card.energy_kind:
                        self.hand_canvas.create_text(
                            x + card_width // 2, y + 55,
                            text=card.energy_kind,
                            fill=text_color,
                            font=("Arial", 9, "bold"),
                            tags=f"card_{i}"
                        )
                
                # インデックス番号（デバッグ用）
                self.hand_canvas.create_text(
                    x + 10, y + 10,
                    text=str(i + 1),
                    fill="white",
                    font=("Arial", 8, "bold"),
                    tags=f"card_{i}"
                )
                
                # クリックイベントのバインド
                if not self.interaction_disabled:
                    self.hand_canvas.tag_bind(f"card_{i}", "<Button-1>", 
                                            lambda e, index=i: self._on_card_click(index))
                    self.hand_canvas.tag_bind(f"card_{i}", "<Enter>", 
                                            lambda e, index=i: self._on_card_hover(index, True))
                    self.hand_canvas.tag_bind(f"card_{i}", "<Leave>", 
                                            lambda e, index=i: self._on_card_hover(index, False))
            
            # キャンバスのスクロール領域を設定
            self.hand_canvas.configure(scrollregion=self.hand_canvas.bbox("all"))
            
        except Exception as e:
            print(f"手札表示更新エラー: {e}")
    
    def _update_hand_info(self, hand_cards: List[Card]):
        """手札情報ラベルを更新"""
        if self.hand_info_label:
            card_count = len(hand_cards)
            
            # カードタイプ別カウント
            pokemon_count = sum(1 for card in hand_cards if card.card_type == CardType.POKEMON)
            trainer_count = sum(1 for card in hand_cards if card.card_type == CardType.TRAINER)
            energy_count = sum(1 for card in hand_cards if card.card_type == CardType.ENERGY)
            
            info_text = f"手札: {card_count}枚"
            if card_count > 0:
                info_text += f" (ポケモン: {pokemon_count}, トレーナー: {trainer_count}, エネルギー: {energy_count})"
            
            self.hand_info_label.config(text=info_text)
    
    def _get_card_color(self, card: Card) -> str:
        """カードタイプに応じた色を取得"""
        color_map = {
            CardType.POKEMON: "#ffcccc",     # 薄いピンク
            CardType.TRAINER: "#ccffcc",     # 薄い緑
            CardType.ENERGY: "#ffffcc",      # 薄い黄色
            CardType.TOOL: "#ccccff"         # 薄い青
        }
        return color_map.get(card.card_type, "#f0f0f0")
    
    def _get_disabled_card_color(self, card: Card) -> str:
        """操作無効化時のカード色を取得"""
        color_map = {
            CardType.POKEMON: "#e0e0e0",
            CardType.TRAINER: "#e0e0e0",
            CardType.ENERGY: "#e0e0e0",
            CardType.TOOL: "#e0e0e0"
        }
        return color_map.get(card.card_type, "#d0d0d0")
    
    def _on_card_click(self, card_index: int):
        """カードクリック時の処理"""
        if not self.interaction_disabled and self.hand_card_click_callback:
            self.hand_card_click_callback(card_index)
    
    def _on_card_hover(self, card_index: int, is_entering: bool):
        """カードホバー時の処理"""
        if self.interaction_disabled:
            return
        
        try:
            tags = f"card_{card_index}"
            if is_entering:
                # マウスオーバー時：カードを少し明るくする
                self.hand_canvas.itemconfig(tags, outline="blue", width=3)
            else:
                # マウスアウト時：元に戻す
                self.hand_canvas.itemconfig(tags, outline="black", width=2)
        except:
            pass  # エラーは無視
    
    def _on_mousewheel(self, event):
        """マウスホイールでの横スクロール"""
        try:
            # 横方向にスクロール
            self.hand_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        except:
            pass  # エラーは無視
    
    def highlight_card(self, card_index: int, highlight: bool = True):
        """特定のカードをハイライト"""
        try:
            tags = f"card_{card_index}"
            if highlight:
                self.hand_canvas.itemconfig(tags, outline="red", width=4)
            else:
                self.hand_canvas.itemconfig(tags, outline="black", width=2)
        except:
            pass  # エラーは無視
    
    def scroll_to_card(self, card_index: int):
        """特定のカードまでスクロール"""
        try:
            card_spacing = 130
            start_x = 10
            target_x = start_x + card_index * card_spacing
            
            # カードが見える位置にスクロール
            canvas_width = self.hand_canvas.winfo_width()
            if target_x > canvas_width:
                scroll_fraction = target_x / (card_spacing * len(self.game_state.player_hand))
                self.hand_canvas.xview_moveto(scroll_fraction)
        except:
            pass  # エラーは無視

    # 廃止されたメソッド名のエイリアス（互換性のため）
    def create_hand_ui(self):
        """廃止予定：setup_hand_uiを使用してください"""
        return self.setup_hand_ui()
    
    def set_card_click_callback(self, callback: Callable[[int], None]):
        """廃止予定：set_callbacksを使用してください"""
        self.set_callbacks(hand_card_click=callback)