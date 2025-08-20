# gui/dialog_manager.py
# Version: 4.32
# Updated: 2025-06-21 13:45
# ダイアログ管理クラス：初期配置UI小型化版

import tkinter as tk
from tkinter import Toplevel, Label, Button, Listbox, messagebox, Frame, Canvas, Scrollbar, Radiobutton, Checkbutton
from typing import List, Callable, Optional, Tuple
from models.card import Card, CardType, TrainerType

class DialogManager:
    """ダイアログ管理クラス（初期配置UI小型化版）"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        # 画面解像度取得
        self.screen_width = parent.winfo_screenwidth()
        self.screen_height = parent.winfo_screenheight()

    def show_initial_pokemon_selection(self, basic_pokemon: List[Card], 
                                     callback: Callable[[int, List[int]], None],
                                     hand_cards: List[Card] = None,
                                     current_mulligans: int = 0,
                                     opponent_mulligans: int = 0,
                                     additional_draw_callback: Callable[[int], None] = None,
                                     draw_executed: bool = False,
                                     mulligan_callback: Callable[[], None] = None):
        """
        初期ポケモン選択ダイアログを表示（マリガン機能付き統合版）
        
        Args:
            basic_pokemon: 選択可能なたねポケモン
            callback: 選択結果のコールバック（バトル場インデックス, ベンチインデックス）
            hand_cards: 現在の手札
            current_mulligans: 現在のマリガン回数
            opponent_mulligans: 相手のマリガン回数
            additional_draw_callback: 追加ドローのコールバック（枚数）
            draw_executed: 追加ドローが実行済みかどうか
            mulligan_callback: マリガン実行のコールバック
        """
        try:
            # 追加ドロー可能枚数を計算
            net_advantage = max(0, opponent_mulligans - current_mulligans) if opponent_mulligans > 0 else 0
            
            # デバッグ出力
            print(f"マリガン回数: プレイヤー={current_mulligans}, 相手={opponent_mulligans}, 追加ドロー可能={net_advantage}")
            
            # 基本ポケモンのフィルタリング
            basic_pokemon = [card for card in basic_pokemon if card.card_type == CardType.POKEMON]
            
            # マリガン判定（たねポケモンがない場合）
            has_basic_pokemon = len(basic_pokemon) > 0
            
            # ダイアログサイズを手札表示に応じて調整
            dialog_width = 850 if hand_cards else 650
            base_height = 450
            if net_advantage > 0 and not draw_executed:
                base_height += 30
            if not has_basic_pokemon:
                base_height += 40  # マリガンエリア分
            dialog_height = base_height
            
            dialog = Toplevel(self.parent)
            dialog.title("初期ポケモン配置")
            dialog.geometry(f"{dialog_width}x{dialog_height}")
            dialog.transient(self.parent)
            dialog.grab_set()
            dialog.resizable(False, False)
            
            # ダイアログ中央配置
            dialog.update_idletasks()
            x = max(25, (self.screen_width // 2) - (dialog_width // 2))
            y = max(25, (self.screen_height // 2) - (dialog_height // 2))
            dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
            
            # ボタンフレーム（上部配置）
            button_frame = Frame(dialog, bg="#f0f0f0")
            button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
            
            # ヘッダー（コンパクト）
            Label(dialog, text="🎮 初期ポケモン配置", 
                  font=("Arial", 14, "bold"), bg="#e6f3ff").pack(fill=tk.X, pady=5)
            
            # マリガンエリア（たねポケモンがない場合）
            if not has_basic_pokemon and mulligan_callback:
                mulligan_frame = Frame(dialog, bg="#ffcccc", relief="ridge", bd=2)
                mulligan_frame.pack(fill=tk.X, padx=15, pady=5)
                
                Label(mulligan_frame, text="⚠️ マリガン（引き直し）", 
                      font=("Arial", 12, "bold"), bg="#ffcccc", fg="red").pack(pady=3)
                Label(mulligan_frame, text="手札にたねポケモンがありません。引き直しが必要です。", 
                      font=("Arial", 10), bg="#ffcccc").pack(pady=2)
                
                mulligan_button_frame = Frame(mulligan_frame, bg="#ffcccc")
                mulligan_button_frame.pack(fill=tk.X, padx=10, pady=5)
                
                def on_mulligan():
                    """マリガン実行"""
                    confirm_text = f"手札を引き直しますか？\n\nマリガン回数: {current_mulligans + 1}"
                    if messagebox.askyesno("マリガン確認", confirm_text):
                        dialog.destroy()
                        mulligan_callback()
                
                Button(mulligan_button_frame, text="引き直し実行", command=on_mulligan,
                       font=("Arial", 10, "bold"), bg="red", fg="white", width=15).pack()
            
            # 追加ドロー用変数
            draw_count_var = tk.IntVar()
            draw_count_var.set(net_advantage)  # デフォルトで最大枚数
            
            # 追加ドロー選択エリア（条件付き表示）
            if net_advantage > 0 and not draw_executed and additional_draw_callback:
                draw_frame = Frame(dialog, bg="#fff2cc", relief="ridge", bd=2)
                draw_frame.pack(fill=tk.X, padx=15, pady=5)
                
                Label(draw_frame, text=f"📝 追加ドロー (最大{net_advantage}枚)", 
                      font=("Arial", 12, "bold"), bg="#fff2cc").pack(pady=3)
                
                draw_selection_frame = Frame(draw_frame, bg="#fff2cc")
                draw_selection_frame.pack(fill=tk.X, padx=10, pady=5)
                
                Label(draw_selection_frame, text="枚数:", 
                      font=("Arial", 10), bg="#fff2cc").pack(side=tk.LEFT, padx=5)
                
                # スピンボックスで枚数選択
                from tkinter import Spinbox
                draw_spinbox = Spinbox(draw_selection_frame, from_=0, to=net_advantage, 
                                     textvariable=draw_count_var, width=5, font=("Arial", 10))
                draw_spinbox.pack(side=tk.LEFT, padx=5)
                
                def on_draw_execute():
                    """追加ドロー実行"""
                    selected_count = draw_count_var.get()
                    if additional_draw_callback and selected_count > 0:
                        additional_draw_callback(selected_count)
                        # ダイアログを閉じて新しいダイアログで再表示
                        dialog.destroy()
                        print(f"追加ドロー実行: {selected_count}枚")
                    else:
                        # ドローしない場合は継続
                        draw_frame.destroy()
                        dialog.geometry(f"{dialog_width}x{base_height}")  # サイズを縮小
                        header_label.config(text="ポケモンを配置してください")
                
                Button(draw_selection_frame, text="ドロー実行", command=on_draw_execute,
                       font=("Arial", 10), bg="yellow", width=10).pack(side=tk.LEFT, padx=10)
                
                header_label = Label(dialog, text="まず追加ドロー枚数を選択してください", 
                      font=("Arial", 10), bg="#e6f3ff")
                header_label.pack(fill=tk.X, pady=2)
            else:
                if has_basic_pokemon:
                    header_text = "ポケモンを配置してください"
                else:
                    header_text = "手札にたねポケモンがありません - 引き直しが必要です"
                    
                header_label = Label(dialog, text=header_text, 
                      font=("Arial", 10), bg="#e6f3ff")
                header_label.pack(fill=tk.X, pady=2)
            
            # メインコンテンツエリア
            content_frame = Frame(dialog)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
            
            # たねポケモンがある場合のみ選択エリアを表示
            if has_basic_pokemon:
                # 横並び配置用フレーム
                selection_container = Frame(content_frame)
                selection_container.pack(fill=tk.BOTH, expand=True)
                
                # バトル場選択エリア（左側）
                battle_frame = Frame(selection_container, relief="solid", bd=1, bg="#ffe6e6")
                if hand_cards:
                    battle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))
                else:
                    battle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
                
                # タイトルの表示分岐（追加ドロー実行後はロック）
                if draw_executed:
                    battle_title = "⚔️ バトル場のポケモン（🔒固定）"
                    battle_subtitle = "※追加ドロー実行後のため変更不可"
                else:
                    battle_title = "⚔️ バトル場のポケモン（1匹選択）"
                    battle_subtitle = ""
                
                Label(battle_frame, text=battle_title, 
                      font=("Arial", 11, "bold"), bg="#ffe6e6").pack(pady=5)
                
                if battle_subtitle:
                    Label(battle_frame, text=battle_subtitle, 
                          font=("Arial", 8), bg="#ffe6e6", fg="red").pack(pady=0)
                
                # バトル場選択用の変数
                battle_selection = tk.IntVar()
                battle_selection.set(0)
                
                # バトル場選択用ラジオボタン（コンパクト）
                battle_list_frame = Frame(battle_frame, bg="#ffe6e6")
                battle_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                # 追加ドロー実行後はバトル場選択をロック
                battle_locked = draw_executed
                
                for i, pokemon in enumerate(basic_pokemon):
                    pokemon_text = f"{pokemon.name} (HP:{pokemon.hp})"
                    if battle_locked and i == 0:
                        pokemon_text += " 🔒"
                    
                    radio = Radiobutton(battle_list_frame, text=pokemon_text, 
                                       variable=battle_selection, value=i,
                                       font=("Arial", 9), bg="#ffe6e6",
                                       wraplength=180 if hand_cards else 250, anchor="w",
                                       state="disabled" if battle_locked and i != 0 else "normal")
                    radio.pack(anchor="w", pady=1)
                
                # ベンチ選択エリア（中央）
                bench_frame = Frame(selection_container, relief="solid", bd=1, bg="#e6ffe6")
                if hand_cards:
                    bench_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(3, 3))
                else:
                    bench_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
                
                Label(bench_frame, text="🏃 ベンチに出すポケモン（最大任意）", 
                      font=("Arial", 11, "bold"), bg="#e6ffe6").pack(pady=5)
                
                # ベンチ選択用の変数
                bench_vars = [tk.BooleanVar() for _ in basic_pokemon]
                
                # ベンチ選択用チェックボタン（コンパクト）
                bench_list_frame = Frame(bench_frame, bg="#e6ffe6")
                bench_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                for i, pokemon in enumerate(basic_pokemon):
                    pokemon_text = f"{pokemon.name} (HP:{pokemon.hp})"
                    check = Checkbutton(bench_list_frame, text=pokemon_text,
                                       variable=bench_vars[i],
                                       font=("Arial", 9), bg="#e6ffe6",
                                       wraplength=180 if hand_cards else 250, anchor="w")
                    check.pack(anchor="w", pady=1)
            
            # 手札確認エリア（右側、条件付き表示）
            if hand_cards:
                hand_frame = Frame(selection_container if has_basic_pokemon else content_frame, 
                                 relief="solid", bd=1, bg="#f0f8ff")
                if has_basic_pokemon:
                    hand_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(3, 0))
                else:
                    hand_frame.pack(fill=tk.BOTH, expand=True)
                
                Label(hand_frame, text=f"📋 現在の手札 ({len(hand_cards)}枚)", 
                      font=("Arial", 11, "bold"), bg="#f0f8ff").pack(pady=5)
                
                # スクロール可能な手札リスト（改善版）
                hand_canvas_frame = Frame(hand_frame, bg="#f0f8ff")
                hand_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                # Canvas と Scrollbar の作成
                hand_canvas = Canvas(hand_canvas_frame, bg="#f0f8ff", height=200, highlightthickness=0)
                hand_scrollbar = Scrollbar(hand_canvas_frame, orient="vertical", command=hand_canvas.yview)
                hand_scrollable_frame = Frame(hand_canvas, bg="#f0f8ff")
                
                # スクロール設定
                def configure_scroll_region(event=None):
                    hand_canvas.configure(scrollregion=hand_canvas.bbox("all"))
                
                hand_scrollable_frame.bind("<Configure>", configure_scroll_region)
                hand_canvas.create_window((0, 0), window=hand_scrollable_frame, anchor="nw")
                hand_canvas.configure(yscrollcommand=hand_scrollbar.set)
                
                # マウスホイールサポート
                def on_mousewheel(event):
                    hand_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                
                def bind_mousewheel(event):
                    hand_canvas.bind_all("<MouseWheel>", on_mousewheel)
                
                def unbind_mousewheel(event):
                    hand_canvas.unbind_all("<MouseWheel>")
                
                hand_canvas.bind('<Enter>', bind_mousewheel)
                hand_canvas.bind('<Leave>', unbind_mousewheel)
                
                # 手札を種類別にグループ化して表示
                card_types = {"POKEMON": [], "ENERGY": [], "TRAINERS": []}
                for card in hand_cards:
                    if card.card_type.value in card_types:
                        card_types[card.card_type.value].append(card)
                    else:
                        card_types["TRAINERS"].append(card)
                
                # 種類別に表示
                for card_type, cards in card_types.items():
                    if cards:
                        # 種類ヘッダー
                        type_label = Label(hand_scrollable_frame, 
                                         text=f"=== {card_type} ({len(cards)}) ===",
                                         font=("Arial", 9, "bold"), bg="#f0f8ff", fg="blue")
                        type_label.pack(anchor="w", padx=5, pady=(5, 2))
                        
                        # カード一覧
                        for card in sorted(cards, key=lambda c: c.name):
                            card_info = f"• {card.name}"
                            if card.card_type.value == "POKEMON" and hasattr(card, 'hp') and card.hp:
                                card_info += f" (HP:{card.hp})"
                            
                            card_label = Label(hand_scrollable_frame, text=card_info,
                                             font=("Arial", 8), bg="#f0f8ff", anchor="w",
                                             wraplength=150 if has_basic_pokemon else 300)
                            card_label.pack(anchor="w", padx=10, pady=1)
                
                # パッキング
                hand_canvas.pack(side="left", fill="both", expand=True)
                hand_scrollbar.pack(side="right", fill="y")
                
                # 初期スクロール領域設定
                hand_frame.update_idletasks()
                configure_scroll_region()
            
            # たねポケモンがある場合のステータス表示と選択機能
            if has_basic_pokemon:
                # ステータス表示
                status_label = Label(dialog, text="", font=("Arial", 10), fg="blue")
                status_label.pack(pady=5)
                
                def update_status():
                    """ステータス更新"""
                    battle_index = battle_selection.get()
                    selected_bench = [i for i, var in enumerate(bench_vars) if var.get()]
                    
                    # バトル場とベンチの重複チェック
                    if battle_index in selected_bench:
                        status_label.config(text="⚠️ バトル場とベンチで同じポケモンが選択されています", fg="red")
                        return False
                    
                    status_label.config(text=f"✅ バトル場: {basic_pokemon[battle_index].name}, ベンチ: {len(selected_bench)}匹", fg="green")
                    return True
                
                def on_selection_change():
                    """選択変更時の処理"""
                    update_status()
                
                # 選択変更時のコールバック設定
                battle_selection.trace("w", lambda *args: on_selection_change())
                for var in bench_vars:
                    var.trace("w", lambda *args: on_selection_change())
                
                def on_confirm():
                    """配置確定"""
                    if not update_status():
                        return
                    
                    battle_index = battle_selection.get()
                    bench_indices = [i for i, var in enumerate(bench_vars) if var.get()]
                    
                    # 最終確認
                    battle_pokemon = basic_pokemon[battle_index].name
                    bench_count = len(bench_indices)
                    
                    confirm_text = f"バトル場: {battle_pokemon}\nベンチ: {bench_count}匹\n\nこの配置で確定しますか？"
                    
                    if messagebox.askyesno("配置確認", confirm_text):
                        dialog.destroy()
                        callback(battle_index, bench_indices)
                
                def on_auto_setup():
                    """自動配置"""
                    # 最もHPの高いポケモンをバトル場に
                    battle_index = 0
                    max_hp = 0
                    for i, pokemon in enumerate(basic_pokemon):
                        if pokemon.hp and pokemon.hp > max_hp:
                            max_hp = pokemon.hp
                            battle_index = i
                    
                    battle_selection.set(battle_index)
                    
                    # 残りのポケモンを最大3匹までベンチに
                    bench_count = 0
                    for i, var in enumerate(bench_vars):
                        if i != battle_index and bench_count < 3:
                            var.set(True)
                            bench_count += 1
                        else:
                            var.set(False)
                    
                    update_status()
                
                # ボタン配置（上部）
                Button(button_frame, text="自動配置", command=on_auto_setup,
                       font=("Arial", 10), bg="lightblue", width=10).pack(side="left", padx=5)
                
                Button(button_frame, text="配置確定", command=on_confirm,
                       font=("Arial", 10, "bold"), bg="lightgreen", width=12).pack(side="right", padx=5)
                
                # 初期ステータス更新
                update_status()
            
            def on_cancel():
                """キャンセル"""
                dialog.destroy()
            
            Button(button_frame, text="キャンセル", command=on_cancel,
                   font=("Arial", 10), bg="lightgray", width=10).pack(side="right", padx=5)
            
        except Exception as e:
            print(f"初期ポケモン選択ダイアログエラー: {e}")
            import traceback
            traceback.print_exc()
            self.show_game_message("エラー", f"ダイアログの作成に失敗しました: {e}")

    def show_additional_draw_selection(self, max_cards: int, callback: Callable[[int], None]):
        """追加ドロー枚数選択ダイアログを表示"""
        try:
            # ダイアログ作成
            dialog = Toplevel(self.parent)
            dialog.title("追加ドロー枚数選択")
            dialog.geometry("400x300")
            dialog.transient(self.parent)
            dialog.grab_set()
            dialog.resizable(False, False)
            
            # ダイアログ中央配置
            dialog.update_idletasks()
            x = max(0, (self.screen_width // 2) - (200))
            y = max(0, (self.screen_height // 2) - (150))
            dialog.geometry(f"400x300+{x}+{y}")
            
            # ヘッダー
            header_frame = Frame(dialog, bg="#fff2cc", relief="raised", bd=2)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            Label(header_frame, text="📝 追加ドロー枚数選択", 
                  font=("Arial", 14, "bold"), bg="#fff2cc").pack(pady=5)
            Label(header_frame, text=f"最大 {max_cards} 枚まで引くことができます", 
                  font=("Arial", 11), bg="#fff2cc").pack(pady=2)
            
            # メインフレーム
            main_frame = Frame(dialog)
            main_frame.pack(fill="both", expand=True, padx=20, pady=15)
            
            # 選択エリア
            selection_frame = Frame(main_frame, relief="ridge", bd=2)
            selection_frame.pack(fill="both", expand=True, pady=(0, 15))
            
            Label(selection_frame, text="ドローする枚数を選択してください", 
                  font=("Arial", 12, "bold")).pack(pady=10)
            
            # リストボックスで枚数選択
            listbox_frame = Frame(selection_frame)
            listbox_frame.pack(fill="both", expand=True, padx=15, pady=10)
            
            scrollbar = Scrollbar(listbox_frame)
            cards_listbox = Listbox(listbox_frame, yscrollcommand=scrollbar.set, 
                                   font=("Arial", 12), height=6, selectmode="single")
            scrollbar.config(command=cards_listbox.yview)
            
            # 0枚から最大枚数までの選択肢を追加
            for i in range(max_cards + 1):
                if i == 0:
                    cards_listbox.insert(tk.END, f"{i} 枚 (ドローしない)")
                else:
                    cards_listbox.insert(tk.END, f"{i} 枚")
            
            # デフォルトで最大枚数を選択
            cards_listbox.selection_set(max_cards)
            
            cards_listbox.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            def on_confirm():
                """確定"""
                selection = cards_listbox.curselection()
                if selection:
                    selected_count = selection[0]  # 0枚から始まるので、そのまま使用
                    dialog.destroy()
                    callback(selected_count)
                else:
                    messagebox.showwarning("選択エラー", "ドロー枚数を選択してください。")
            
            def on_cancel():
                """キャンセル"""
                dialog.destroy()
                callback(0)  # キャンセル時は0枚
            
            # ボタンフレーム
            button_frame = Frame(main_frame)
            button_frame.pack(fill="x")
            
            Button(button_frame, text="キャンセル", command=on_cancel,
                   font=("Arial", 11), width=10, height=2).pack(side="right", padx=5)
            
            Button(button_frame, text="ドロー実行", command=on_confirm,
                   font=("Arial", 11, "bold"), bg="lightgreen", width=12, height=2).pack(side="right", padx=5)
            
        except Exception as e:
            print(f"追加ドロー選択ダイアログエラー: {e}")
            import traceback
            traceback.print_exc()
            callback(0)

    def _handle_additional_draw(self, selected_count: int, current_dialog):
        """追加ドロー処理とダイアログ管理"""
        try:
            if selected_count > 0 and self._additional_draw_callback:
                # 追加ドロー実行
                self._additional_draw_callback(selected_count)
                
                # 現在のダイアログを閉じる
                if current_dialog and current_dialog.winfo_exists():
                    current_dialog.destroy()
                
                print(f"追加ドロー実行: {selected_count}枚 - 古いダイアログを閉じました")
            else:
                print("追加ドローをスキップしました")
                
        except Exception as e:
            print(f"追加ドロー処理エラー: {e}")
            import traceback
            traceback.print_exc()
        """ベンチポケモン選択ダイアログを表示（にげる用）"""
        try:
            if not bench_options:
                self.show_game_message("にげる失敗", "ベンチにポケモンがいません。")
                callback(None)
                return
            
            # ダイアログ作成
            dialog = Toplevel(self.parent)
            dialog.title(f"にげる - 交代ポケモン選択")
            dialog_width, dialog_height = 600, 500
            dialog.geometry(f"{dialog_width}x{dialog_height}")
            dialog.transient(self.parent)
            dialog.grab_set()
            
            # ダイアログ中央配置
            dialog.update_idletasks()
            x = max(0, (self.screen_width // 2) - (dialog_width // 2))
            y = max(0, (self.screen_height // 2) - (dialog_height // 2))
            dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
            
            # ヘッダー
            header_frame = Frame(dialog, bg="#ffe6e6", relief="raised", bd=2)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            Label(header_frame, text="🏃 にげる - 交代ポケモン選択", 
                  font=("Arial", 16, "bold"), bg="#ffe6e6").pack(pady=5)
            
            retreat_info = f"{retreating_pokemon.name}がにげます"
            if retreat_cost > 0:
                retreat_info += f" (コスト: エネルギー{retreat_cost}個)"
            else:
                retreat_info += f" (コスト: なし)"
            
            Label(header_frame, text=retreat_info, 
                  font=("Arial", 12), bg="#ffe6e6").pack(pady=2)
            Label(header_frame, text="バトル場に出すポケモンを選択してください", 
                  font=("Arial", 11), bg="#ffe6e6").pack(pady=2)
            
            # メインフレーム
            main_frame = Frame(dialog)
            main_frame.pack(fill="both", expand=True, padx=15, pady=10)
            
            # ポケモン選択エリア
            selection_frame = Frame(main_frame, relief="ridge", bd=2)
            selection_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            Label(selection_frame, text="🎯 交代ポケモン選択", 
                  font=("Arial", 14, "bold")).pack(pady=8)
            
            # 選択用の変数
            bench_selection = tk.IntVar()
            bench_selection.set(0)  # デフォルトで最初のポケモンを選択
            
            # スクロール可能なフレーム
            canvas = Canvas(selection_frame, height=250)
            scrollbar = Scrollbar(selection_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # ベンチポケモン選択用ラジオボタン
            for i, (bench_index, pokemon) in enumerate(bench_options):
                # ポケモン情報の構築
                pokemon_info = f"{pokemon.name}"
                
                # HP情報
                if pokemon.hp:
                    current_hp = pokemon.hp - getattr(pokemon, 'damage_taken', 0)
                    pokemon_info += f" (HP: {current_hp}/{pokemon.hp})"
                
                # タイプ情報
                if hasattr(pokemon, 'pokemon_type') and pokemon.pokemon_type:
                    pokemon_info += f" [{pokemon.pokemon_type}]"
                
                # エネルギー情報
                energy_count = getattr(pokemon, 'attached_energy', [])
                if energy_count:
                    pokemon_info += f" (エネルギー: {len(energy_count)}個)"
                
                radio = Radiobutton(scrollable_frame, text=pokemon_info,
                                   variable=bench_selection, value=i,
                                   font=("Arial", 12), anchor="w",
                                   wraplength=500)
                radio.pack(fill="x", padx=15, pady=5)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # ボタンフレーム
            button_frame = Frame(main_frame)
            button_frame.pack(fill="x", pady=10)
            button_frame.pack_propagate(False)
            
            def on_retreat():
                """にげる実行"""
                selected_index = bench_selection.get()
                if 0 <= selected_index < len(bench_options):
                    bench_index, selected_pokemon = bench_options[selected_index]
                    
                    # 確認ダイアログ
                    confirm_text = f"{retreating_pokemon.name}がにげて、{selected_pokemon.name}がバトル場に出ます。"
                    if retreat_cost > 0:
                        confirm_text += f"\n\nエネルギー{retreat_cost}個を支払います。"
                    confirm_text += "\n\nよろしいですか？"
                    
                    if messagebox.askyesno("にげる確認", confirm_text):
                        dialog.destroy()
                        callback(bench_index)
                else:
                    messagebox.showwarning("選択エラー", "有効なポケモンを選択してください。")
            
            def on_cancel():
                """キャンセル"""
                dialog.destroy()
                callback(None)
            
            # ボタン配置
            Button(button_frame, text="キャンセル", command=on_cancel,
                   font=("Arial", 12), width=12, height=2).pack(side="right", padx=5)
            
            Button(button_frame, text="にげる実行", command=on_retreat,
                   font=("Arial", 12, "bold"), bg="orange", width=14, height=2).pack(side="right", padx=5)
        
        except Exception as e:
            print(f"ベンチポケモン選択ダイアログエラー: {e}")
            import traceback
            traceback.print_exc()
            callback(None)

    def show_game_message(self, title: str, message: str):
        """ゲームメッセージダイアログを表示"""
        messagebox.showinfo(title, message)

    def show_card_list(self, title: str, cards: List[Card]):
        """カード一覧ダイアログを表示"""
        if not cards:
            self.show_game_message(title, "カードがありません。")
            return
        
        # ダイアログ作成
        dialog = Toplevel(self.parent)
        dialog.title(title)
        dialog.geometry("600x500")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # ダイアログ中央配置
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # ヘッダー
        header_frame = Frame(dialog, bg="#e6f3ff", relief="raised", bd=2)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        Label(header_frame, text=f"📋 {title}", 
              font=("Arial", 16, "bold"), bg="#e6f3ff").pack(pady=5)
        Label(header_frame, text=f"合計 {len(cards)} 枚", 
              font=("Arial", 12), bg="#e6f3ff").pack(pady=2)
        
        # カードリストフレーム
        list_frame = Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # スクロール可能なリストボックス
        listbox_frame = Frame(list_frame)
        listbox_frame.pack(fill="both", expand=True)
        
        scrollbar = Scrollbar(listbox_frame)
        card_listbox = Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        scrollbar.config(command=card_listbox.yview)
        
        # カードを分類してリストに追加
        card_types = {}
        for card in cards:
            card_type = card.card_type.value
            if card_type not in card_types:
                card_types[card_type] = []
            card_types[card_type].append(card)
        
        # タイプ別にソートして表示
        for card_type in sorted(card_types.keys()):
            card_listbox.insert(tk.END, f"=== {card_type} ===")
            for card in sorted(card_types[card_type], key=lambda c: c.name):
                card_info = f"  {card.name}"
                if card.card_type == CardType.POKEMON and card.hp:
                    card_info += f" (HP: {card.hp})"
                card_listbox.insert(tk.END, card_info)
            card_listbox.insert(tk.END, "")  # 空行
        
        card_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 閉じるボタン
        Button(dialog, text="閉じる", command=dialog.destroy,
               font=("Arial", 12), width=15, height=2).pack(pady=10)

    def show_card_selection(self, title: str, cards: List[Card], 
                           callback: Callable[[Optional[int]], None]):
        """カード選択ダイアログを表示"""
        if not cards:
            self.show_game_message(title, "選択可能なカードがありません。")
            callback(None)
            return
        
        # ダイアログ作成
        dialog = Toplevel(self.parent)
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # ダイアログ中央配置
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # ヘッダー
        Label(dialog, text=title, font=("Arial", 16, "bold")).pack(pady=10)
        
        # カード選択リスト
        listbox_frame = Frame(dialog)
        listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = Scrollbar(listbox_frame)
        card_listbox = Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        scrollbar.config(command=card_listbox.yview)
        
        for i, card in enumerate(cards):
            card_info = f"{i+1}. {card.name}"
            if card.card_type == CardType.POKEMON and card.hp:
                card_info += f" (HP: {card.hp})"
            card_listbox.insert(tk.END, card_info)
        
        card_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_select():
            """選択実行"""
            selection = card_listbox.curselection()
            if selection:
                selected_index = selection[0]
                dialog.destroy()
                callback(selected_index)
            else:
                messagebox.showwarning("選択エラー", "カードを選択してください。")
        
        def on_cancel():
            """キャンセル"""
            dialog.destroy()
            callback(None)
        
        # ボタンフレーム
        button_frame = Frame(dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        Button(button_frame, text="キャンセル", command=on_cancel,
               font=("Arial", 12), width=10).pack(side="right", padx=5)
        
        Button(button_frame, text="選択", command=on_select,
               font=("Arial", 12), bg="lightgreen", width=10).pack(side="right", padx=5)