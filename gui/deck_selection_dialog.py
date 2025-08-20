# gui/deck_selection_dialog.py
# Version: 4.21
# Updated: 2025-06-15 18:30
# デッキ選択ダイアログ：選択状態独立管理修正版

import tkinter as tk
from tkinter import Toplevel, Label, Button, Listbox, SINGLE, messagebox, Frame
from typing import Callable, Dict
import random

class DeckSelectionDialog:
    """デッキ選択ダイアログクラス（選択状態独立管理修正版）"""
    
    def __init__(self, parent: tk.Tk, database_manager):
        self.parent = parent
        self.database_manager = database_manager
        self.dialog = None
        self.callback = None
        
        # 画面解像度を取得
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()
        
        # ダイアログサイズを画面解像度に応じて調整
        self.dialog_width = min(850, int(self.screen_width * 0.65))
        self.dialog_height = min(800, int(self.screen_height * 0.85))
        
        # 最小サイズ保証
        self.dialog_width = max(self.dialog_width, 800)
        self.dialog_height = max(self.dialog_height, 750)
        
        # 🆕 独立したデッキデータ管理（修正）
        self.player_deck_ids = []     # プレイヤー用デッキIDリスト
        self.opponent_deck_ids = []   # 対戦相手用デッキIDリスト
        self.available_decks = {}     # 利用可能なデッキ情報
        
        # 🆕 選択状態管理（修正）
        self.player_last_selection = None    # プレイヤーの最後の選択
        self.opponent_last_selection = None  # 対戦相手の最後の選択
        
        print(f"画面解像度: {self.screen_width}x{self.screen_height}")
        print(f"デッキ選択ダイアログサイズ: {self.dialog_width}x{self.dialog_height}")
    
    def show(self, callback: Callable[[int, int], None]):
        """デッキ選択ダイアログを表示（独立選択修正版）"""
        self.callback = callback
        
        # 利用可能なデッキを取得
        self.available_decks = self.database_manager.get_available_decks()
        
        if not self.available_decks:
            messagebox.showerror("エラー", "利用可能なデッキがありません。\ncardsフォルダにdeck.csvファイルを配置してください。")
            return
        
        # 🆕 デッキIDリストを独立して初期化（修正）
        self._initialize_deck_lists()
        
        # ダイアログ作成
        self.dialog = Toplevel(self.parent)
        self.dialog.title("ポケモンカードゲーム - デッキ選択")
        self.dialog.geometry(f"{self.dialog_width}x{self.dialog_height}")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # ダイアログ中央配置
        self.dialog.update_idletasks()
        x = max(0, (self.screen_width // 2) - (self.dialog_width // 2))
        y = max(0, (self.screen_height // 2) - (self.dialog_height // 2))
        
        # 画面外に出ないよう調整
        margin = 50
        x = max(margin, min(x, self.screen_width - self.dialog_width - margin))
        y = max(margin, min(y, self.screen_height - self.dialog_height - margin))
        
        self.dialog.geometry(f"{self.dialog_width}x{self.dialog_height}+{x}+{y}")
        self.dialog.minsize(800, 750)
        
        # ダイアログUI設定
        self._setup_dialog_ui()
    
    def _initialize_deck_lists(self):
        """🆕 デッキリストを独立して初期化（修正）"""
        try:
            # プレイヤー用と対戦相手用で独立したデッキIDリストを作成
            for deck_id in self.available_decks.keys():
                self.player_deck_ids.append(deck_id)
                self.opponent_deck_ids.append(deck_id)
            
            print(f"デッキリスト初期化完了:")
            print(f"  プレイヤー用: {len(self.player_deck_ids)}個")
            print(f"  対戦相手用: {len(self.opponent_deck_ids)}個")
            
        except Exception as e:
            print(f"デッキリスト初期化エラー: {e}")
    
    def _setup_dialog_ui(self):
        """ダイアログUIをセットアップ（独立選択修正版）"""
        # ヘッダー
        header_height = max(100, int(self.dialog_height * 0.15))
        header_frame = Frame(self.dialog, bg="#e6f3ff", relief="raised", bd=2, height=header_height)
        header_frame.pack(fill="x", padx=15, pady=10)
        header_frame.pack_propagate(False)
        
        subtitle_font_size = 12
        Label(header_frame, text="デッキを選択してゲームを開始してください", 
            font=("Arial", subtitle_font_size), bg="#e6f3ff").pack(pady=8)
        
        # メインフレーム（左右分割）
        main_frame = Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        # 左側フレーム（プレイヤー）
        left_frame = Frame(main_frame, relief="ridge", bd=2)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 右側フレーム（対戦相手）
        right_frame = Frame(main_frame, relief="ridge", bd=2)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # プレイヤーデッキ選択部分を作成
        self._create_player_deck_selection(left_frame)
        
        # 対戦相手デッキ選択部分を作成
        self._create_opponent_deck_selection(right_frame)
        
        # ボタンフレーム
        self._create_button_frame()
    
    def _create_player_deck_selection(self, parent_frame):
        """🆕 プレイヤー用デッキ選択UIを作成（修正）"""
        try:
            label_font_size = 12
            Label(parent_frame, text="あなたが使用するデッキを選択:", 
                font=("Arial", label_font_size, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            # プレイヤー用リストフレーム
            player_list_frame = Frame(parent_frame)
            player_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            listbox_font_size = 10
            listbox_height = max(8, int(self.dialog_height / 60))
            
            # 🆕 プレイヤー用リストボックス（独立管理）
            self.player_deck_listbox = Listbox(
                player_list_frame, 
                selectmode=SINGLE, 
                height=listbox_height, 
                font=("Arial", listbox_font_size), 
                relief="sunken", 
                bd=2,
                exportselection=False  # 🆕 重要：他のリストボックスとの選択状態干渉を防ぐ
            )
            
            player_scrollbar = tk.Scrollbar(player_list_frame, orient="vertical", command=self.player_deck_listbox.yview)
            self.player_deck_listbox.configure(yscrollcommand=player_scrollbar.set)
            
            # 🆕 プレイヤー用リストボックスにデッキを追加
            self._populate_player_deck_list()
            
            # 🆕 プレイヤー用選択変更イベントをバインド（修正）
            self.player_deck_listbox.bind('<<ListboxSelect>>', self._on_player_selection_change)
            
            # 🆕 プレイヤー側：デフォルト選択（修正）
            if self.player_deck_ids:
                self.player_deck_listbox.selection_set(0)
                self.player_last_selection = 0
            
            self.player_deck_listbox.pack(side="left", fill="both", expand=True)
            player_scrollbar.pack(side="right", fill="y")
            
            # プレイヤー用ランダム選択チェックボックス
            self.player_random_mode = tk.BooleanVar(value=False)
            tk.Checkbutton(
                parent_frame, 
                text="ランダムにデッキを選択", 
                variable=self.player_random_mode,
                command=self._on_player_random_change,
                font=("Arial", 10)
            ).pack(anchor="w", padx=10, pady=5)
            
        except Exception as e:
            print(f"プレイヤーデッキ選択UI作成エラー: {e}")
    
    def _create_opponent_deck_selection(self, parent_frame):
        """🆕 対戦相手用デッキ選択UIを作成（修正）"""
        try:
            label_font_size = 12
            Label(parent_frame, text="対戦相手が使用するデッキを選択:", 
                font=("Arial", label_font_size, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            # 対戦相手用リストフレーム
            opponent_list_frame = Frame(parent_frame)
            opponent_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            listbox_font_size = 10
            listbox_height = max(8, int(self.dialog_height / 60))
            
            # 🆕 対戦相手用リストボックス（独立管理）
            self.opponent_deck_listbox = Listbox(
                opponent_list_frame, 
                selectmode=SINGLE, 
                height=listbox_height, 
                font=("Arial", listbox_font_size), 
                relief="sunken", 
                bd=2,
                exportselection=False  # 🆕 重要：他のリストボックスとの選択状態干渉を防ぐ
            )
            
            opponent_scrollbar = tk.Scrollbar(opponent_list_frame, orient="vertical", command=self.opponent_deck_listbox.yview)
            self.opponent_deck_listbox.configure(yscrollcommand=opponent_scrollbar.set)
            
            # 🆕 対戦相手用リストボックスにデッキを追加
            self._populate_opponent_deck_list()
            
            # 🆕 対戦相手用選択変更イベントをバインド（修正）
            self.opponent_deck_listbox.bind('<<ListboxSelect>>', self._on_opponent_selection_change)
            
            # 🆕 対戦相手側：デフォルト選択（修正）
            if self.opponent_deck_ids:
                self.opponent_deck_listbox.selection_set(0)
                self.opponent_last_selection = 0
            
            self.opponent_deck_listbox.pack(side="left", fill="both", expand=True)
            opponent_scrollbar.pack(side="right", fill="y")
            
            # 対戦相手用ランダム選択チェックボックス
            self.opponent_random_mode = tk.BooleanVar(value=False)
            tk.Checkbutton(
                parent_frame, 
                text="ランダムにデッキを選択", 
                variable=self.opponent_random_mode,
                command=self._on_opponent_random_change,
                font=("Arial", 10)
            ).pack(anchor="w", padx=10, pady=5)
            
        except Exception as e:
            print(f"対戦相手デッキ選択UI作成エラー: {e}")
    
    def _populate_player_deck_list(self):
        """🆕 プレイヤー用リストボックスにデッキを追加（修正）"""
        try:
            for deck_id in self.player_deck_ids:
                deck_name = self.available_decks.get(deck_id, f"デッキ {deck_id}")
                deck_cards = self.database_manager.get_deck_cards(deck_id)
                total_cards = sum(count for _, count in deck_cards)
                
                # カード種別集計
                pokemon_count = sum(count for card, count in deck_cards if card.card_type.name == "POKEMON")
                trainer_count = sum(count for card, count in deck_cards if card.card_type.name == "TRAINER")
                energy_count = sum(count for card, count in deck_cards if card.card_type.name == "ENERGY")
                
                display_text = f"{deck_name} (ID: {deck_id})\n"
                display_text += f"総カード数: {total_cards}枚\n"
                display_text += f"ポケモン: {pokemon_count} | トレーナー: {trainer_count} | エネルギー: {energy_count}"
                
                self.player_deck_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            print(f"プレイヤーデッキリスト追加エラー: {e}")
    
    def _populate_opponent_deck_list(self):
        """🆕 対戦相手用リストボックスにデッキを追加（修正）"""
        try:
            for deck_id in self.opponent_deck_ids:
                deck_name = self.available_decks.get(deck_id, f"デッキ {deck_id}")
                deck_cards = self.database_manager.get_deck_cards(deck_id)
                total_cards = sum(count for _, count in deck_cards)
                
                # カード種別集計
                pokemon_count = sum(count for card, count in deck_cards if card.card_type.name == "POKEMON")
                trainer_count = sum(count for card, count in deck_cards if card.card_type.name == "TRAINER")
                energy_count = sum(count for card, count in deck_cards if card.card_type.name == "ENERGY")
                
                display_text = f"{deck_name} (ID: {deck_id})\n"
                display_text += f"総カード数: {total_cards}枚\n"
                display_text += f"ポケモン: {pokemon_count} | トレーナー: {trainer_count} | エネルギー: {energy_count}"
                
                self.opponent_deck_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            print(f"対戦相手デッキリスト追加エラー: {e}")
    
    def _on_player_selection_change(self, event):
        """🆕 プレイヤーの選択変更時の処理（修正）"""
        try:
            selection = self.player_deck_listbox.curselection()
            if selection:
                # ランダム選択モードでない場合のみ選択を記録
                if not self.player_random_mode.get():
                    self.player_last_selection = selection[0]
                    print(f"プレイヤー選択変更: インデックス {selection[0]} (デッキID: {self.player_deck_ids[selection[0]]})")
                
        except Exception as e:
            print(f"プレイヤー選択変更エラー: {e}")
    
    def _on_opponent_selection_change(self, event):
        """🆕 対戦相手の選択変更時の処理（修正）"""
        try:
            selection = self.opponent_deck_listbox.curselection()
            if selection:
                # ランダム選択モードでない場合のみ選択を記録
                if not self.opponent_random_mode.get():
                    self.opponent_last_selection = selection[0]
                    print(f"対戦相手選択変更: インデックス {selection[0]} (デッキID: {self.opponent_deck_ids[selection[0]]})")
                
        except Exception as e:
            print(f"対戦相手選択変更エラー: {e}")
    
    def _on_player_random_change(self):
        """🆕 プレイヤーのランダム選択状態変更時の処理（修正）"""
        try:
            if self.player_random_mode.get():
                # ランダム選択ON：リストボックスを無効化し、選択をクリア
                self.player_deck_listbox.selection_clear(0, tk.END)
                self.player_deck_listbox.configure(state="disabled")
                print("プレイヤー: ランダム選択モードON")
            else:
                # ランダム選択OFF：リストボックスを有効化し、前回の選択を復元
                self.player_deck_listbox.configure(state="normal")
                if self.player_last_selection is not None and self.player_deck_ids:
                    self.player_deck_listbox.selection_set(self.player_last_selection)
                elif self.player_deck_ids:
                    self.player_deck_listbox.selection_set(0)
                    self.player_last_selection = 0
                print("プレイヤー: ランダム選択モードOFF")
                
        except Exception as e:
            print(f"プレイヤーランダム選択変更エラー: {e}")
    
    def _on_opponent_random_change(self):
        """🆕 対戦相手のランダム選択状態変更時の処理（修正）"""
        try:
            if self.opponent_random_mode.get():
                # ランダム選択ON：リストボックスを無効化し、選択をクリア
                self.opponent_deck_listbox.selection_clear(0, tk.END)
                self.opponent_deck_listbox.configure(state="disabled")
                print("対戦相手: ランダム選択モードON")
            else:
                # ランダム選択OFF：リストボックスを有効化し、前回の選択を復元
                self.opponent_deck_listbox.configure(state="normal")
                if self.opponent_last_selection is not None and self.opponent_deck_ids:
                    self.opponent_deck_listbox.selection_set(self.opponent_last_selection)
                elif self.opponent_deck_ids:
                    self.opponent_deck_listbox.selection_set(0)
                    self.opponent_last_selection = 0
                print("対戦相手: ランダム選択モードOFF")
                
        except Exception as e:
            print(f"対戦相手ランダム選択変更エラー: {e}")
    
    def _create_button_frame(self):
        """ボタンフレームを作成"""
        # ボタンフレーム
        button_height = max(80, int(self.dialog_height * 0.12))
        button_frame = Frame(self.dialog, height=button_height)
        button_frame.pack(fill="x", padx=20, pady=20)
        button_frame.pack_propagate(False)
        
        # ボタンサイズを画面に応じて調整
        button_font_size = min(14, max(11, int(self.dialog_width / 60)))
        button_width = max(14, int(self.dialog_width / 55))
        
        # ボタン配置
        left_button_frame = Frame(button_frame)
        left_button_frame.pack(side="left", fill="y")
        
        right_button_frame = Frame(button_frame)
        right_button_frame.pack(side="right", fill="y")
        
        # 左側ボタン
        Button(left_button_frame, text="デッキ詳細", command=self._show_deck_details,
            font=("Arial", button_font_size), bg="lightblue", width=button_width, height=2).pack(side="left", padx=10)
        
        # 右側ボタン
        Button(right_button_frame, text="キャンセル", command=self._on_cancel,
            font=("Arial", button_font_size), width=button_width, height=2).pack(side="right", padx=10)
        
        Button(right_button_frame, text="ゲーム開始", command=self._on_start_game,
            font=("Arial", button_font_size + 1, "bold"), bg="lightgreen", 
            width=int(button_width * 1.2), height=2).pack(side="right", padx=10)
    
    def _show_deck_details(self):
        """🆕 選択されたデッキの詳細を表示（独立選択対応修正版）"""
        try:
            # プレイヤー側と対戦相手側の選択状態を確認
            player_selection = self.player_deck_listbox.curselection() if not self.player_random_mode.get() else None
            opponent_selection = self.opponent_deck_listbox.curselection() if not self.opponent_random_mode.get() else None
            
            # どちらが選択されているかを判定（優先順位：最後にクリックされた方）
            deck_id = None
            deck_type = None
            
            # フォーカスを持つリストボックスを判定
            focused_widget = self.dialog.focus_get()
            
            if focused_widget == self.player_deck_listbox and player_selection:
                deck_id = self.player_deck_ids[player_selection[0]]
                deck_type = "プレイヤー"
            elif focused_widget == self.opponent_deck_listbox and opponent_selection:
                deck_id = self.opponent_deck_ids[opponent_selection[0]]
                deck_type = "対戦相手"
            elif player_selection:  # フォーカス判定ができない場合はプレイヤーを優先
                deck_id = self.player_deck_ids[player_selection[0]]
                deck_type = "プレイヤー"
            elif opponent_selection:
                deck_id = self.opponent_deck_ids[opponent_selection[0]]
                deck_type = "対戦相手"
            else:
                messagebox.showwarning("警告", "詳細を表示するデッキを選択してください")
                return
            
            # デッキ詳細を表示
            self._display_deck_details(deck_id, deck_type)
            
        except Exception as e:
            print(f"デッキ詳細表示エラー: {e}")
            messagebox.showerror("エラー", f"デッキ詳細の表示中にエラーが発生しました: {e}")
    
    def _display_deck_details(self, deck_id: int, deck_type: str):
        """🆕 デッキ詳細ウィンドウを表示（修正）"""
        try:
            deck_cards = self.database_manager.get_deck_cards(deck_id)
            
            # 詳細ウィンドウサイズを画面解像度に応じて調整
            detail_width = min(800, int(self.screen_width * 0.55))
            detail_height = min(700, int(self.screen_height * 0.75))
            
            # 詳細ウィンドウ作成
            detail_window = Toplevel(self.dialog)
            detail_window.title(f"デッキ詳細 - {deck_type}デッキ {deck_id}")
            detail_window.geometry(f"{detail_width}x{detail_height}")
            detail_window.transient(self.dialog)
            
            # 中央配置
            detail_window.update_idletasks()
            x = max(25, (self.screen_width // 2) - (detail_width // 2))
            y = max(25, (self.screen_height // 2) - (detail_height // 2))
            x = max(25, min(x, self.screen_width - detail_width - 25))
            y = max(25, min(y, self.screen_height - detail_height - 25))
            detail_window.geometry(f"{detail_width}x{detail_height}+{x}+{y}")
            
            # ヘッダー
            header_font_size = min(18, max(14, int(detail_width / 40)))
            Label(detail_window, text=f"{deck_type}デッキ {deck_id} の構成", 
                font=("Arial", header_font_size, "bold")).pack(pady=20)
            
            # カードリスト
            list_frame = Frame(detail_window)
            list_frame.pack(fill="both", expand=True, padx=25, pady=20)
            
            listbox_font_size = min(12, max(10, int(detail_width / 60)))
            
            card_listbox = Listbox(list_frame, font=("Arial", listbox_font_size))
            scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=card_listbox.yview)
            card_listbox.configure(yscrollcommand=scrollbar.set)
            
            # カードタイプ別集計
            pokemon_count = 0
            trainer_count = 0
            energy_count = 0
            total_count = 0
            
            # カードリストに追加
            for card, count in deck_cards:
                card_info = f"{card.name} × {count} ({card.card_type.value})"
                if card.card_type.name == "POKEMON" and card.hp:
                    card_info += f" HP:{card.hp}"
                    if hasattr(card, 'pokemon_type') and card.pokemon_type:
                        card_info += f" [{card.pokemon_type}]"
                
                card_listbox.insert(tk.END, card_info)
                
                # 集計
                total_count += count
                if card.card_type.name == "POKEMON":
                    pokemon_count += count
                elif card.card_type.name == "TRAINER":
                    trainer_count += count
                elif card.card_type.name == "ENERGY":
                    energy_count += count
            
            card_listbox.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # 統計情報
            stats_frame = Frame(detail_window, bg="#f5f5f5", relief="ridge", bd=2)
            stats_frame.pack(fill="x", padx=25, pady=20)
            
            stats_font_size = min(14, max(11, int(detail_width / 55)))
            
            Label(stats_frame, text="デッキ統計", font=("Arial", stats_font_size + 2, "bold"), bg="#f5f5f5").pack(pady=10)
            Label(stats_frame, text=f"総カード数: {total_count}枚", bg="#f5f5f5", 
                font=("Arial", stats_font_size)).pack(pady=2)
            Label(stats_frame, text=f"ポケモン: {pokemon_count}枚 | トレーナー: {trainer_count}枚 | エネルギー: {energy_count}枚", 
                bg="#f5f5f5", font=("Arial", stats_font_size)).pack(pady=2)
            
            # バランス評価
            balance_text = "良好" if 15 <= pokemon_count <= 25 and 8 <= trainer_count <= 18 and 6 <= energy_count <= 12 else "要確認"
            balance_color = "green" if balance_text == "良好" else "orange"
            Label(stats_frame, text=f"デッキバランス: {balance_text}", bg="#f5f5f5", 
                font=("Arial", stats_font_size), fg=balance_color).pack(pady=2)
            
            Button(detail_window, text="閉じる", command=detail_window.destroy,
                font=("Arial", stats_font_size), height=2).pack(pady=20)
                
        except Exception as e:
            print(f"デッキ詳細ウィンドウ表示エラー: {e}")
            messagebox.showerror("エラー", f"デッキ詳細の表示中にエラーが発生しました: {e}")
    
    def _on_start_game(self):
        """🆕 ゲーム開始ボタンが押された時の処理（独立選択対応修正版）"""
        try:
            # プレイヤーデッキの決定
            if self.player_random_mode.get():
                # ランダム選択
                player_deck_id = random.choice(self.player_deck_ids)
                print(f"プレイヤーデッキ（ランダム選択）: ID {player_deck_id}")
            else:
                # リストボックスから選択
                player_selection = self.player_deck_listbox.curselection()
                if not player_selection:
                    messagebox.showwarning("警告", "プレイヤーのデッキを選択してください")
                    return
                player_deck_id = self.player_deck_ids[player_selection[0]]
                print(f"プレイヤーデッキ（手動選択）: ID {player_deck_id}")
            
            # 対戦相手デッキの決定
            if self.opponent_random_mode.get():
                # ランダム選択
                opponent_deck_id = random.choice(self.opponent_deck_ids)
                print(f"対戦相手デッキ（ランダム選択）: ID {opponent_deck_id}")
            else:
                # リストボックスから選択
                opponent_selection = self.opponent_deck_listbox.curselection()
                if not opponent_selection:
                    messagebox.showwarning("警告", "対戦相手のデッキを選択してください")
                    return
                opponent_deck_id = self.opponent_deck_ids[opponent_selection[0]]
                print(f"対戦相手デッキ（手動選択）: ID {opponent_deck_id}")
            
            # デッキの有効性チェック
            if not self._validate_decks(player_deck_id, opponent_deck_id):
                return
            
            # ダイアログを閉じてコールバック実行
            self.dialog.destroy()
            if self.callback:
                self.callback(player_deck_id, opponent_deck_id)
                
        except Exception as e:
            print(f"ゲーム開始処理エラー: {e}")
            messagebox.showerror("エラー", f"ゲーム開始処理中にエラーが発生しました: {e}")
    
    def _validate_decks(self, player_deck_id: int, opponent_deck_id: int) -> bool:
        """🆕 デッキの有効性をチェック（修正）"""
        try:
            # デッキの有効性チェック
            player_cards = self.database_manager.get_deck_cards(player_deck_id)
            opponent_cards = self.database_manager.get_deck_cards(opponent_deck_id)
            
            if not player_cards:
                messagebox.showerror("エラー", f"プレイヤーデッキ(ID: {player_deck_id})が空です")
                return False
            
            if not opponent_cards:
                messagebox.showerror("エラー", f"相手デッキ(ID: {opponent_deck_id})が空です")
                return False
            
            return True
            
        except Exception as e:
            print(f"デッキ検証エラー: {e}")
            messagebox.showerror("エラー", f"デッキの検証中にエラーが発生しました: {e}")
            return False
    
    def _on_cancel(self):
        """キャンセルボタンが押された時の処理"""
        try:
            self.dialog.destroy()
        except Exception as e:
            print(f"キャンセル処理エラー: {e}")
