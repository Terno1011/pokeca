# gui/main_gui.py
# Version: 4.31
# Updated: 2025-06-14 12:15
# メインGUI：にげるシステム完全統合版

import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

from gui.deck_selection_dialog import DeckSelectionDialog
from gui.battle_field_ui import BattleFieldUI
from gui.hand_ui import HandUI
from gui.dialog_manager import DialogManager
from gui.attack_selection_dialog import AttackSelectionDialog
from gui.game_controller import GameController
from gui.card_actions import CardActions
from gui.ai_controller import AIController
from models.game_state import GameState
from models.card import Card, CardType

class PokemonTCGGUI:
    """ポケモンTCGシミュレータのメインGUIクラス（にげるシステム完全統合版）"""
    
    def __init__(self, root: tk.Tk, database_manager):
        self.root = root
        self.database_manager = database_manager
        
        # ゲーム状態とコントローラーの初期化
        self.game_state = GameState()
        self.game_controller = GameController(self.game_state, database_manager)
        self.dialog_manager = DialogManager(root)
        self.card_actions = CardActions(self.game_state)
        self.ai_controller = AIController(self.game_state, self.card_actions)
        
        # 🆕 ダイアログマネージャーを各コントローラーに設定
        self.card_actions.set_dialog_manager(self.dialog_manager)
        self.game_controller.set_dialog_manager(self.dialog_manager)
        
        # 🔥 バグ修正：UI更新コールバックを設定
        self.card_actions.update_display_callback = self._update_display
        
        # ワザ選択ダイアログ
        self.attack_selection_dialog = AttackSelectionDialog(root)
        
        # 初期セットアップフラグ
        self.waiting_for_initial_setup = False
        self.player_initial_setup_complete = False
        self.opponent_initial_setup_complete = False
        
        # ターン管理フラグ
        self.ai_turn_in_progress = False
        
        # UIコンポーネント
        self.battle_field_ui = None
        self.hand_ui = None
        
        self._setup_ui()
        
        # デッキ選択ダイアログを表示
        self._show_deck_selection()

    def _setup_ui(self):
        """UIの初期セットアップ"""
        self.root.title("ポケモンカードゲーム シミュレータ v4.31 - にげるシステム完全統合版")
        
        # 画面解像度を取得して動的にサイズ調整
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # メインウィンドウサイズを画面解像度に応じて調整
        window_width = min(1700, int(screen_width * 0.95))
        window_height = min(1100, int(screen_height * 0.95))
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg="#f0f0f0")
        
        print(f"メインウィンドウサイズ: {window_width}x{window_height}")
        
        # メインフレーム
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # バトルフィールドUIのセットアップ
        self.battle_field_ui = BattleFieldUI(main_frame, self.game_state)
        
        # バトルフィールドUI用のコールバック設定（ターン終了コールバック追加）
        self.battle_field_ui.set_callbacks(
            on_field_card_click=self._on_field_card_clicked,
            on_deck_click=self._on_deck_clicked,
            on_discard_click=self._on_discard_clicked,
            on_side_click=self._on_side_clicked,
            on_trash_click=self._on_trash_clicked,
            on_pokemon_attack=self._on_pokemon_attack_requested,
            on_end_turn=self._on_end_turn_clicked  # 🆕 ターン終了コールバック追加
        )

        # 🆕 スタジアムクリックコールバックを設定
        self.battle_field_ui.set_stadium_click_callback(self._on_stadium_clicked)
        
        # バトルフィールドの作成
        battle_field_frame = self.battle_field_ui.create_battle_field()
        battle_field_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 🆕 にげるコールバックを設定（v4.31追加）
        if hasattr(self.battle_field_ui, 'context_menu') and self.battle_field_ui.context_menu:
            self.battle_field_ui.context_menu.set_callbacks(
                attack_callback=self._on_pokemon_attack_requested,
                ability_callback=self._on_pokemon_ability_requested,
                retreat_callback=self._on_pokemon_retreat_requested,  # 🆕 新規追加
                details_callback=self._on_pokemon_details_requested
            )
        
        # 手札UIのセットアップ（スペースを詰める）
        hand_frame = tk.Frame(main_frame, bg="#e6e6fa", height=200)
        hand_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))  # 上のpadyを10から5に変更
        hand_frame.pack_propagate(False)
        
        self.hand_ui = HandUI(hand_frame, self.game_state)
        self.hand_ui.set_callbacks(hand_card_click=self._on_hand_card_clicked)
        
        hand_ui_frame = self.hand_ui.setup_hand_ui()
        if hand_ui_frame:
            hand_ui_frame.pack(fill=tk.BOTH, expand=True)
            print("手札UI初期化完了")
        else:
            print("警告: 手札UIの作成に失敗しました")
        
        # ステータス表示ラベル（下部に配置）
        status_frame = tk.Frame(main_frame, bg="#f0f0f0")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(3, 0))
        
        self.status_label = tk.Label(
            status_frame,
            text="デッキを選択してください",
            bg="#f0f0f0",
            font=("Arial", 12),
            anchor="w"
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _create_battle_log_area(self, parent_frame):
        """🆕 バトルログエリアを作成"""
        try:
            # バトルログヘッダー
            log_header = tk.Frame(parent_frame, bg="#e6f3ff", relief="raised", bd=1)
            log_header.pack(fill=tk.X, pady=(0, 5))
            
            tk.Label(log_header, text="バトルログ", 
                    font=("Arial", 12, "bold"), bg="#e6f3ff").pack(pady=5)
            
            # バトルログメインエリア
            log_main_frame = tk.Frame(parent_frame, relief="sunken", bd=2)
            log_main_frame.pack(fill=tk.BOTH, expand=True)
            
            # スクロール可能なテキストエリア
            log_text_frame = tk.Frame(log_main_frame)
            log_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # テキストウィジェットとスクロールバー
            self.battle_log_text = tk.Text(
                log_text_frame, 
                wrap=tk.WORD, 
                font=("Arial", 9),
                bg="white",
                fg="black",
                state=tk.DISABLED,  # 編集不可
                height=25,
                width=30
            )
            
            log_scrollbar = tk.Scrollbar(log_text_frame, orient="vertical", 
                                       command=self.battle_log_text.yview)
            self.battle_log_text.configure(yscrollcommand=log_scrollbar.set)
            
            self.battle_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # ログクリアボタン
            log_button_frame = tk.Frame(parent_frame)
            log_button_frame.pack(fill=tk.X, pady=(5, 0))
            
            tk.Button(log_button_frame, text="ログクリア", 
                     command=self._clear_battle_log,
                     font=("Arial", 9), bg="lightgray", width=12).pack()
            
            # 初期メッセージ
            self._add_battle_log("ゲーム開始準備中...")
            
            print("バトルログエリア初期化完了")
            
        except Exception as e:
            print(f"バトルログエリア作成エラー: {e}")

    def _add_battle_log(self, message: str):
        """🆕 バトルログにメッセージを追加"""
        try:
            if hasattr(self, 'battle_log_text'):
                self.battle_log_text.config(state=tk.NORMAL)
                
                # タイムスタンプ付きでメッセージを追加
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                log_entry = f"[{timestamp}] {message}\n"
                
                self.battle_log_text.insert(tk.END, log_entry)
                self.battle_log_text.see(tk.END)  # 最新メッセージまでスクロール
                
                self.battle_log_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"バトルログ追加エラー: {e}")

    def _clear_battle_log(self):
        """🆕 バトルログをクリア"""
        try:
            if hasattr(self, 'battle_log_text'):
                self.battle_log_text.config(state=tk.NORMAL)
                self.battle_log_text.delete(1.0, tk.END)
                self.battle_log_text.config(state=tk.DISABLED)
                self._add_battle_log("ログがクリアされました")
        except Exception as e:
            print(f"バトルログクリアエラー: {e}")

    def _show_deck_selection(self):
        """デッキ選択ダイアログの表示"""
        try:
            deck_dialog = DeckSelectionDialog(self.root, self.database_manager)
            deck_dialog.show(callback=self._on_deck_selected)
        
        except Exception as e:
            print(f"デッキ選択ダイアログ表示エラー: {e}")
            messagebox.showerror("エラー", f"デッキ選択の初期化に失敗しました: {e}")

    def _on_deck_selected(self, player_deck_id: int, opponent_deck_id: int):
        """デッキ選択完了時の処理"""
        try:
            print(f"デッキ選択完了: プレイヤー={player_deck_id}, 相手={opponent_deck_id}")
            
            # ゲーム初期化
            success = self.game_controller.initialize_game(player_deck_id, opponent_deck_id)
            
            if success:
                # 🔧 修正：status_labelの存在確認
                if hasattr(self, 'status_label') and self.status_label:
                    self.status_label.config(text="初期ポケモンを配置してください")
                
                # 🆕 バトルログに記録
                if hasattr(self, 'battle_log_text'):
                    self._add_battle_log("ゲーム初期化完了")
                    self._add_battle_log("初期ポケモンを配置してください")
                
                self._start_initial_setup()
            else:
                messagebox.showerror("エラー", "ゲームの初期化に失敗しました")
        
        except Exception as e:
            print(f"デッキ選択処理エラー: {e}")
            messagebox.showerror("エラー", f"デッキ選択の処理中にエラーが発生しました: {e}")    

    def _start_initial_setup(self):
        """初期セットアップの開始（追加ドロー選択統合版）"""
        try:
            self.waiting_for_initial_setup = True
            
            # プレイヤーの基本ポケモンを取得
            basic_pokemon = [card for card in self.game_state.player_hand if 
                        card.card_type == CardType.POKEMON and 
                        getattr(card, 'evolve_step', 0) == 0]
            
            if not basic_pokemon:
                # マリガン処理は既にゲーム初期化時に完了しているはず
                messagebox.showerror("エラー", "マリガン処理後も手札にたねポケモンがありません。")
                return
            
            current_mulligans = getattr(self.game_state, 'player_mulligans', 0)
            opponent_mulligans = getattr(self.game_state, 'opponent_mulligans', 0)
            
            # 初期ポケモン選択ダイアログを表示（追加ドロー選択統合版）
            self.dialog_manager.show_initial_pokemon_selection(
                basic_pokemon=basic_pokemon,
                callback=self._on_initial_pokemon_selected,
                hand_cards=self.game_state.player_hand.copy(),
                current_mulligans=current_mulligans,
                opponent_mulligans=opponent_mulligans,
                additional_draw_callback=self._on_additional_draw_requested
            )
        
        except Exception as e:
            print(f"初期セットアップ開始エラー: {e}")
            messagebox.showerror("エラー", f"初期セットアップの開始に失敗しました: {e}")

    def _on_additional_draw_requested(self, draw_count: int):
        """追加ドロー要求時の処理（ダイヤログ再表示対応）"""
        try:
            if draw_count > 0:
                # 追加ドロー実行
                success = self.game_controller.execute_additional_draw(draw_count)
                if success:
                    # 🔧 修正：status_labelの存在確認
                    if hasattr(self, 'status_label') and self.status_label:
                        self.status_label.config(text=f"追加で{draw_count}枚ドローしました。ポケモンを配置してください")
                    
                    # 🆕 バトルログに記録
                    if hasattr(self, 'battle_log_text'):
                        self._add_battle_log(f"追加で{draw_count}枚ドローしました")
                    
                    # UIを更新
                    self._update_display()
                    
                    # 新しい手札でダイヤログを再表示
                    self._restart_initial_setup_with_updated_hand()
                else:
                    messagebox.showerror("エラー", "追加ドローの実行に失敗しました")
                    # エラー時も再表示
                    self._restart_initial_setup_with_updated_hand()
            else:
                # 追加ドローしない場合
                if hasattr(self, 'status_label') and self.status_label:
                    self.status_label.config(text="初期ポケモンを配置してください")
        
        except Exception as e:
            print(f"追加ドロー処理エラー: {e}")
            messagebox.showerror("エラー", f"追加ドローの処理中にエラーが発生しました: {e}")
            # エラー時も再表示を試行
            self._restart_initial_setup_with_updated_hand()

    def _on_initial_pokemon_selected(self, battle_index: int, bench_indices: List[int]):
        """初期ポケモン選択完了時の処理"""
        try:
            # プレイヤーの基本ポケモンを取得 - 修正
            basic_pokemon = [card for card in self.game_state.player_hand if 
                        card.card_type == CardType.POKEMON and 
                        getattr(card, 'evolve_step', 0) == 0]
            
            # バトル場に配置
            battle_pokemon = basic_pokemon[battle_index]
            self.game_state.player_active = battle_pokemon
            self.game_state.player_hand.remove(battle_pokemon)
            
            # ベンチに配置
            self.game_state.player_bench = [None] * 5
            for i, bench_index in enumerate(bench_indices):
                if i < 5:  # ベンチの上限
                    bench_pokemon = basic_pokemon[bench_index]
                    self.game_state.player_bench[i] = bench_pokemon
                    self.game_state.player_hand.remove(bench_pokemon)
            
            print(f"初期配置完了: バトル場={battle_pokemon.name}, ベンチ={len(bench_indices)}匹")
            
            # 相手（AI）の初期セットアップ
            self._setup_opponent_initial_pokemon()
            
            # 初期セットアップ完了
            self.waiting_for_initial_setup = False
            self.player_initial_setup_complete = True
            self.opponent_initial_setup_complete = True
            
            # 先攻を決定（プレイヤーが先攻）
            self.game_state.set_first_player("player")
            self.game_state.current_player = "player"
            self.game_state.turn_count = 1
            self.game_state.initialization_complete = True
            
            # 初回のターン開始処理を実行（ドロー処理含む）
            turn_messages, can_continue = self.game_controller.start_turn("player")
            if not can_continue:
                # 山札切れによる敗北
                message_text = "\n".join(turn_messages)
                self.dialog_manager.show_game_message("ゲーム終了", message_text)
                self._handle_game_over("opponent")  # プレイヤーが負け
                return
            elif turn_messages:
                message_text = "\n".join(turn_messages)
                self.dialog_manager.show_game_message("ターン開始", message_text)
            
            # ゲーム開始
            # 🔧 修正：status_labelの存在確認
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.config(text="ゲーム開始 - あなたのターンです")
            
            # 🆕 バトルログに記録
            if hasattr(self, 'battle_log_text'):
                self._add_battle_log("ゲーム開始！")
                self._add_battle_log("あなたのターンです")
            
            # 🆕 にげるコールバックを再設定（v4.31追加）
            self._setup_retreat_callbacks()
            
            print("🎮 初期セットアップ完了 - ゲーム開始！")
            self._update_display()
        
        except Exception as e:
            print(f"初期セットアップ完了エラー: {e}")

    def _restart_initial_setup_with_updated_hand(self):
        """更新された手札で初期セットアップダイヤログを再表示（追加ドロー実行済み版）"""
        try:
            # プレイヤーの基本ポケモンを取得（最新の手札から）
            basic_pokemon = [card for card in self.game_state.player_hand if 
                        card.card_type == CardType.POKEMON and 
                        getattr(card, 'evolve_step', 0) == 0]
            
            if not basic_pokemon:
                messagebox.showerror("エラー", "追加ドロー後も手札にたねポケモンがありません。")
                return
            
            current_mulligans = getattr(self.game_state, 'player_mulligans', 0)
            opponent_mulligans = getattr(self.game_state, 'opponent_mulligans', 0)
            
            print(f"手札更新後の再表示: たねポケモン{len(basic_pokemon)}匹, 手札{len(self.game_state.player_hand)}枚")
            
            # 初期ポケモン選択ダイヤログを再表示（更新された手札で、追加ドロー実行済み）
            self.dialog_manager.show_initial_pokemon_selection(
                basic_pokemon=basic_pokemon,
                callback=self._on_initial_pokemon_selected,
                hand_cards=self.game_state.player_hand.copy(),  # 最新の手札
                current_mulligans=current_mulligans,
                opponent_mulligans=opponent_mulligans,
                additional_draw_callback=self._on_additional_draw_requested,
                draw_executed=True  # 🆕 追加ドロー実行済みフラグ
            )
        
        except Exception as e:
            print(f"初期セットアップ再表示エラー: {e}")
            messagebox.showerror("エラー", f"初期セットアップの再表示に失敗しました: {e}")

    def _setup_retreat_callbacks(self):
        """にげるコールバックの設定（v4.31新規追加）"""
        try:
            if hasattr(self.battle_field_ui, 'context_menu') and self.battle_field_ui.context_menu:
                self.battle_field_ui.context_menu.set_callbacks(
                    attack_callback=self._on_pokemon_attack_requested,
                    ability_callback=self._on_pokemon_ability_requested,
                    retreat_callback=self._on_pokemon_retreat_requested,
                    details_callback=self._on_pokemon_details_requested
                )
                print("✅ にげるコールバック設定完了")
        
        except Exception as e:
            print(f"にげるコールバック設定エラー: {e}")
    
    def _setup_opponent_initial_pokemon(self):
        """相手（AI）の初期ポケモンをセットアップ"""
        try:
            # 相手の基本ポケモンを取得 - 修正
            opponent_basic = [card for card in self.game_state.opponent_hand if 
                            card.card_type == CardType.POKEMON and 
                            getattr(card, 'evolve_step', 0) == 0]
            
            if opponent_basic:
                # バトル場に配置（最初のポケモン）
                self.game_state.opponent_active = opponent_basic[0]
                self.game_state.opponent_hand.remove(opponent_basic[0])
                
                # ベンチに配置（残りのポケモンを最大3匹）
                self.game_state.opponent_bench = [None] * 5
                for i, pokemon in enumerate(opponent_basic[1:4]):  # 最大3匹
                    self.game_state.opponent_bench[i] = pokemon
                    self.game_state.opponent_hand.remove(pokemon)
                
                print(f"相手初期配置完了: バトル場={self.game_state.opponent_active.name}")
        
        except Exception as e:
            print(f"相手初期セットアップエラー: {e}")
            
    def _on_pokemon_attack_requested(self, pokemon: Card, attack_index: int):
        """ポケモンの攻撃要求処理（デバッグ強化版）"""
        try:
            print(f"🔍 攻撃要求デバッグ開始: {pokemon.name}, ワザ{attack_index}")
            
            # ポケモンのワザ情報をデバッグ出力
            print(f"  - attack_name: {getattr(pokemon, 'attack_name', 'なし')}")
            print(f"  - attack2_name: {getattr(pokemon, 'attack2_name', 'なし')}")
            print(f"  - attack_power: {getattr(pokemon, 'attack_power', 'なし')}")
            print(f"  - attack2_power: {getattr(pokemon, 'attack2_power', 'なし')}")
            
            # エネルギー装着状況をデバッグ出力
            attached_energy = getattr(pokemon, 'attached_energy', [])
            print(f"  - 装着エネルギー数: {len(attached_energy)}")
            for i, energy in enumerate(attached_energy):
                energy_type = getattr(energy, 'energy_kind', energy.name)
                print(f"    {i+1}. {energy_type}")
            
            if self.game_state.current_player != "player":
                self.dialog_manager.show_game_message(
                    "ターン制限", 
                    "相手のターンです。攻撃はできません。"
                )
                return
            
            if self.ai_turn_in_progress:
                self.dialog_manager.show_game_message(
                    "AI行動中", 
                    "相手の行動が進行中です。お待ちください。"
                )
                return
            
            if self.waiting_for_initial_setup:
                self.dialog_manager.show_game_message(
                    "初期セットアップ中", 
                    "初期ポケモンの配置を完了してください。"
                )
                return
            
            # 先攻1ターン目の攻撃制限チェック
            if self.game_state.is_first_player_first_turn():
                self.dialog_manager.show_game_message(
                    "攻撃制限", 
                    "先攻プレイヤーの最初のターンは攻撃できません。"
                )
                return
            
            # 攻撃済みチェック
            if getattr(self.game_state, 'player_has_attacked', False):
                self.dialog_manager.show_game_message(
                    "攻撃制限", 
                    "このターンはすでに攻撃しました。"
                )
                return
            
            print(f"攻撃要求: {pokemon.name}でワザ{attack_index}番を使用")
            
            # エネルギーコスト事前チェック
            from utils.energy_cost_checker import EnergyCostChecker
            can_use, cost_message = EnergyCostChecker.can_use_attack(pokemon, attack_index, self.game_state)
            print(f"  - エネルギーコスト判定: {can_use}, メッセージ: {cost_message}")
            
            if not can_use:
                self.dialog_manager.show_game_message(
                    "エネルギー不足",
                    f"「{pokemon.name}」のワザが使用できません。\n\n{cost_message}"
                )
                return
            
            # CardActionsを使用して攻撃を実行
            pokemon_pos = self._find_pokemon_position(pokemon)
            if not pokemon_pos:
                self.dialog_manager.show_game_message(
                    "攻撃失敗", 
                    "攻撃するポケモンが見つかりません。"
                )
                return
            
            print(f"  - ポケモン位置: {pokemon_pos}")
            
            result = self.card_actions.use_pokemon_attack(pokemon_pos, attack_index)
            
            if result.get("success", False):
                # 攻撃成功時のメッセージ表示
                attack_message = result.get("message", "攻撃を実行しました")
                self.dialog_manager.show_game_message("攻撃結果", attack_message)
                
                # 画面更新
                self._update_display()
                
                # 攻撃後、プレイヤーのターンを自動終了
                print("⚔️ 攻撃完了 - 自動でターンを終了します")
                self.root.after(1000, self._on_end_turn_clicked)
                
            else:
                # 攻撃失敗時のメッセージ
                error_message = result.get("message", "攻撃に失敗しました")
                self.dialog_manager.show_game_message("攻撃失敗", error_message)
        
        except Exception as e:
            print(f"攻撃要求処理エラー: {e}")
            import traceback
            traceback.print_exc()
            self.dialog_manager.show_game_message("攻撃エラー", f"攻撃処理中にエラーが発生しました: {e}")

    def _on_pokemon_ability_requested(self, pokemon: Card):
        """ポケモンの特性使用要求処理"""
        try:
            print(f"特性使用要求: {pokemon.name}")
            self.dialog_manager.show_game_message(
                "特性",
                f"{pokemon.name}の特性使用は未実装です。"
            )
        
        except Exception as e:
            print(f"特性使用要求処理エラー: {e}")
    
    # 🆕 にげる要求処理（v4.31新規追加）
    def _on_pokemon_retreat_requested(self, pokemon: Card):
        """ポケモンのにげる要求処理（v4.31新規追加）"""
        try:
            print(f"🏃 にげる要求: {pokemon.name}")
            
            # 基本的な前提条件チェック
            if self.game_state.current_player != "player":
                self.dialog_manager.show_game_message(
                    "ターン制限", 
                    "相手のターンです。にげることはできません。"
                )
                return
            
            if self.ai_turn_in_progress:
                self.dialog_manager.show_game_message(
                    "AI行動中", 
                    "相手の行動が進行中です。お待ちください。"
                )
                return
            
            if self.waiting_for_initial_setup:
                self.dialog_manager.show_game_message(
                    "初期セットアップ中", 
                    "初期ポケモンの配置を完了してください。"
                )
                return
            
            # バトル場のポケモンかチェック
            if pokemon != self.game_state.player_active:
                self.dialog_manager.show_game_message(
                    "にげる制限",
                    "バトル場のポケモンのみがにげることができます。"
                )
                return
            
            # CardActionsを使用してにげる処理を実行
            result = self.card_actions.retreat_pokemon(pokemon)
            
            if result.get("success", False):
                # にげる成功
                retreat_message = result.get("message", "にげることに成功しました")
                self.dialog_manager.show_game_message("にげる成功", retreat_message)
                
                # 画面更新
                self._update_display()
                
            elif result.get("requires_choice", False):
                # ベンチポケモン選択が必要
                bench_options = result.get("bench_options", [])
                retreat_cost = result.get("retreat_cost", 0)
                
                if bench_options:
                    print(f"ベンチポケモン選択ダイアログを表示: {len(bench_options)}匹の選択肢")
                    self.dialog_manager.show_bench_pokemon_selection_for_retreat(
                        pokemon, bench_options, retreat_cost, 
                        lambda selected_index: self._on_bench_pokemon_selected_for_retreat(pokemon, selected_index)
                    )
                else:
                    self.dialog_manager.show_game_message("にげる失敗", "ベンチに交代できるポケモンがいません")
            else:
                # にげる失敗
                error_message = result.get("message", "にげることに失敗しました")
                self.dialog_manager.show_game_message("にげる失敗", error_message)
        
        except Exception as e:
            print(f"にげる要求処理エラー: {e}")
            import traceback
            traceback.print_exc()
            self.dialog_manager.show_game_message("にげるエラー", f"にげる処理中にエラーが発生しました: {e}")
    
    def _on_bench_pokemon_selected_for_retreat(self, retreating_pokemon: Card, selected_bench_index: Optional[int]):
        """ベンチポケモン選択完了時のコールバック（v4.31新規追加）"""
        try:
            if selected_bench_index is None:
                print("にげる処理がキャンセルされました")
                return
            
            print(f"ベンチポケモン選択完了: インデックス{selected_bench_index}")
            
            # 選択されたベンチポケモンとの交代でにげる処理を実行
            result = self.card_actions.retreat_pokemon_with_choice(retreating_pokemon, selected_bench_index)
            
            if result.get("success", False):
                # にげる成功
                retreat_message = result.get("message", "にげることに成功しました")
                self.dialog_manager.show_game_message("にげる成功", retreat_message)
                
                # 画面更新
                self._update_display()
                
                print("✅ にげる処理完了")
                
            else:
                # にげる失敗
                error_message = result.get("message", "にげることに失敗しました")
                self.dialog_manager.show_game_message("にげる失敗", error_message)
        
        except Exception as e:
            print(f"ベンチポケモン選択コールバックエラー: {e}")
            import traceback
            traceback.print_exc()
            self.dialog_manager.show_game_message("にげるエラー", f"にげる処理中にエラーが発生しました: {e}")
    
    def _on_pokemon_details_requested(self, pokemon: Card):
        """ポケモン詳細表示要求処理"""
        try:
            self._show_pokemon_details(pokemon)
        
        except Exception as e:
            print(f"ポケモン詳細表示エラー: {e}")
    
    def _find_pokemon_position(self, pokemon: Card) -> Optional[str]:
        """ポケモンの位置を特定"""
        try:
            # バトル場をチェック
            if self.game_state.player_active == pokemon:
                return "active"
            
            # ベンチをチェック
            for i, bench_pokemon in enumerate(self.game_state.player_bench):
                if bench_pokemon == pokemon:
                    return f"bench_{i}"
            
            return None
        
        except Exception as e:
            print(f"ポケモン位置特定エラー: {e}")
            return None
    
    def _on_field_card_clicked(self, side: str, location: str, index: Optional[int], action: str = "show_details"):
        """フィールドカードクリック時の処理"""
        try:
            print(f"フィールドカードクリック: {side}-{location}-{index}, アクション: {action}")
            
            if action == "show_details":
                # カード詳細を表示
                pokemon = self._get_pokemon_at_location(side, location, index)
                if pokemon:
                    print(f"詳細表示対象: {pokemon.name} at {side}-{location}-{index}")
                    self._show_pokemon_details(pokemon, side, location, index)
                else:
                    print(f"警告: 指定位置にポケモンが見つかりません: {side}-{location}-{index}")
            
            elif action.startswith("attack_"):
                # 攻撃処理
                attack_number = int(action.split("_")[1])
                pokemon = self._get_pokemon_at_location(side, location, index)
                if pokemon:
                    self._on_pokemon_attack_requested(pokemon, attack_number)
        
        except Exception as e:
            print(f"フィールドカードクリック処理エラー: {e}")
    
    def _get_pokemon_at_location(self, side: str, location: str, index: Optional[int]) -> Optional[Card]:
        """指定された位置のポケモンを取得"""
        try:
            if side == "player":
                if location == "active":
                    return self.game_state.player_active
                elif location == "bench" and index is not None:
                    if 0 <= index < len(self.game_state.player_bench):
                        return self.game_state.player_bench[index]
            elif side == "opponent":
                if location == "active":
                    return self.game_state.opponent_active
                elif location == "bench" and index is not None:
                    if 0 <= index < len(self.game_state.opponent_bench):
                        return self.game_state.opponent_bench[index]
            
            return None
        
        except Exception as e:
            print(f"ポケモン取得エラー: {e}")
            return None
    
    def _show_pokemon_details(self, pokemon: Card, side: str = "", location: str = "", index: Optional[int] = None):
        """ポケモンの詳細を表示"""
        try:
            # DialogManagerのshow_card_detailsメソッドを呼び出し
            if hasattr(self.dialog_manager, 'show_card_details'):
                self.dialog_manager.show_card_details(pokemon, side, location, index)
            else:
                # フォールバック：簡易表示
                self._show_simple_pokemon_details(pokemon, side, location, index)
        
        except Exception as e:
            print(f"ポケモン詳細表示エラー: {e}")
            # エラー時のフォールバック
            self._show_simple_pokemon_details(pokemon, side, location, index)
    
    def _show_simple_pokemon_details(self, pokemon: Card, side: str = "", location: str = "", index: Optional[int] = None):
        """簡易ポケモン詳細表示（フォールバック用）"""
        try:
            details = f"【{pokemon.name}】\n"
            details += f"カードID: {pokemon.id}\n"
            
            if hasattr(pokemon, 'hp') and pokemon.hp:
                details += f"HP: {pokemon.hp}\n"
            
            if hasattr(pokemon, 'pokemon_type') and pokemon.pokemon_type:
                details += f"タイプ: {pokemon.pokemon_type}\n"
            
            # 位置情報
            if side and location:
                if location == "active":
                    position_text = f"{side}のバトル場"
                elif location == "bench" and index is not None:
                    position_text = f"{side}のベンチ{index + 1}"
                else:
                    position_text = f"{side}の{location}"
                details += f"位置: {position_text}\n"
            
            # ワザ情報（安全に取得）
            attacks_info = self._get_pokemon_attacks_info(pokemon)
            if attacks_info:
                details += f"\n{attacks_info}"
            
            # 特性情報
            if hasattr(pokemon, 'ability_name') and pokemon.ability_name:
                details += f"\n特性: {pokemon.ability_name}"
                if hasattr(pokemon, 'ability_description') and pokemon.ability_description:
                    details += f"\n効果: {pokemon.ability_description}"
            
            # エネルギー装着状況
            energy_count = len(getattr(pokemon, 'attached_energy', []))
            if energy_count > 0:
                details += f"\n装着エネルギー: {energy_count}個"
            
            # にげるコスト表示
            retreat_cost = getattr(pokemon, 'retreat_cost', 0) or 0
            details += f"\nにげるコスト: {retreat_cost}個"
            
            print(f"ポケモン詳細表示: {pokemon.name}")
            messagebox.showinfo(f"{pokemon.name} の詳細", details)
        
        except Exception as e:
            print(f"簡易ポケモン詳細表示エラー: {e}")
            messagebox.showerror("エラー", "ポケモンの詳細表示に失敗しました")
    
    def _get_pokemon_attacks_info(self, pokemon: Card) -> str:
        """ポケモンのワザ情報を安全に取得（旧形式統一版）"""
        try:
            attacks_info = ""
            
            # 旧形式のワザ情報のみを処理
            if hasattr(pokemon, 'attack_name') and pokemon.attack_name:
                attacks_info += f"ワザ1: {pokemon.attack_name}"
                if hasattr(pokemon, 'attack_power') and pokemon.attack_power:
                    attacks_info += f" ({pokemon.attack_power}ダメージ)"
                attacks_info += "\n"
            
            if hasattr(pokemon, 'attack2_name') and pokemon.attack2_name:
                attacks_info += f"ワザ2: {pokemon.attack2_name}"
                if hasattr(pokemon, 'attack2_power') and pokemon.attack2_power:
                    attacks_info += f" ({pokemon.attack2_power}ダメージ)"
                attacks_info += "\n"
            
            return attacks_info.strip()
        except Exception as e:
            print(f"ワザ情報取得エラー: {e}")
            return ""

    def _on_hand_card_clicked(self, card_index: int):
        """手札カードクリック時の処理"""
        try:
            if self.waiting_for_initial_setup:
                return
            
            if self.game_state.current_player != "player":
                self.dialog_manager.show_game_message("ターン制限", "相手のターンです")
                return
            
            if card_index >= len(self.game_state.player_hand):
                print(f"無効なカードインデックス: {card_index}")
                return
            
            card = self.game_state.player_hand[card_index]
            print(f"手札カードクリック: {card.name}")
            
            # CardActionsを使用してカードを使用
            result_message = self.card_actions.play_card_from_hand(card_index)
            print(f"カード使用結果: {result_message}")
            
            # 結果をダイアログで表示（エネルギー装着選択等は別途ダイアログで処理）
            if "選択してください" not in result_message:
                self.dialog_manager.show_game_message("カード使用", result_message)
            
            # 画面更新
            self._update_display()
        
        except Exception as e:
            print(f"手札カードクリック処理エラー: {e}")
            self.dialog_manager.show_game_message("エラー", f"カード使用中にエラーが発生しました: {e}")
    
    def _on_deck_clicked(self, side: str):
        """山札クリック時の処理"""
        try:
            if side == "player":
                deck_size = len(self.game_state.player_deck)
                self.dialog_manager.show_game_message("山札", f"プレイヤーの山札: {deck_size}枚")
            else:
                deck_size = len(self.game_state.opponent_deck)
                self.dialog_manager.show_game_message("山札", f"相手の山札: {deck_size}枚")
        
        except Exception as e:
            print(f"山札クリック処理エラー: {e}")
    
    def _on_discard_clicked(self, side: str):
        """捨て札クリック時の処理"""
        try:
            if side == "player":
                discard_pile = self.game_state.player_discard
                title = "プレイヤーの捨て札"
            else:
                discard_pile = self.game_state.opponent_discard
                title = "相手の捨て札"
            
            if discard_pile:
                self.dialog_manager.show_card_list(title, discard_pile)
            else:
                self.dialog_manager.show_game_message(title, "捨て札はありません")
        
        except Exception as e:
            print(f"捨て札クリック処理エラー: {e}")
    
    def _on_side_clicked(self, side: str):
        """サイドクリック時の処理"""
        try:
            if side == "player":
                side_cards = getattr(self.game_state, 'player_side', [])
                title = "プレイヤーのサイド"
            else:
                side_cards = getattr(self.game_state, 'opponent_side', [])
                title = "相手のサイド"
            
            side_count = len(side_cards)
            self.dialog_manager.show_game_message(title, f"サイド: {side_count}枚")
        
        except Exception as e:
            print(f"サイドクリック処理エラー: {e}")
    
    def _on_trash_clicked(self, side: str):
        """トラッシュクリック時の処理"""
        try:
            # トラッシュ機能は現在未実装
            self.dialog_manager.show_game_message("トラッシュ", "トラッシュ機能は未実装です")
        
        except Exception as e:
            print(f"トラッシュクリック処理エラー: {e}")
    
      
    def _on_stadium_clicked(self, stadium_card=None):
        """🆕 スタジアムクリック時の処理"""
        try:
            if stadium_card:
                # スタジアムカードの詳細表示
                card_info = f"スタジアム: {stadium_card.name}"
                
                # 効果説明を追加
                if hasattr(stadium_card, 'ability_description') and stadium_card.ability_description:
                    card_info += f"\n\n効果:\n{stadium_card.ability_description}"
                else:
                    card_info += f"\n\n効果: まだ実装されていません"
                
                # カードの詳細情報を追加
                card_info += f"\n\nカード情報:"
                card_info += f"\n・カードタイプ: スタジアム"
                card_info += f"\n・カードID: {stadium_card.id}"
                
                self.dialog_manager.show_game_message("スタジアム詳細", card_info)
            else:
                # スタジアムが設置されていない場合
                info = "現在スタジアムは設置されていません。\n\n"
                info += "スタジアムカードを手札から使用することで、\n"
                info += "スタジアムを設置できます。"
                self.dialog_manager.show_game_message("スタジアム", info)
        
        except Exception as e:
            print(f"スタジアムクリック処理エラー: {e}")
            self.dialog_manager.show_game_message("エラー", f"スタジアム表示中にエラーが発生しました: {e}")
    
    
    def _on_end_turn_clicked(self):
        """ターン終了ボタンクリック時の処理"""
        try:
            if self.waiting_for_initial_setup:
                self.dialog_manager.show_game_message("初期セットアップ中", "初期セットアップを完了してください")
                return
            
            if self.ai_turn_in_progress:
                return
            
            if self.game_state.current_player != "player":
                self.dialog_manager.show_game_message("ターン制限", "現在は相手のターンです")
                return
            
            print("プレイヤーのターン終了")
            
            # プレイヤーのターン終了処理
            self.game_controller.end_turn("player")
            
            # 相手（AI）のターン開始
            self.game_state.current_player = "opponent"
            self.game_state.turn_count += 1
            self.status_label.config(text="相手のターンです...")
            self.ai_turn_in_progress = True
            
            # 画面更新
            self._update_display()
            
            # AI行動を少し遅延して実行
            self.root.after(1000, self._execute_ai_turn)
        
        except Exception as e:
            print(f"ターン終了処理エラー: {e}")
            self.dialog_manager.show_game_message("エラー", f"ターン終了処理中にエラーが発生しました: {e}")
    
    def _execute_ai_turn(self):
        """AIのターン実行"""
        try:
            print("🤖 AIのターン開始")
            
            # AIターン開始処理
            turn_messages, can_continue = self.game_controller.start_turn("opponent")
            if not can_continue:
                # 山札切れによる敗北
                message_text = "\n".join(turn_messages)
                self.dialog_manager.show_game_message("ゲーム終了", message_text)
                self._handle_game_over("player")  # 相手が負け（プレイヤーが勝ち）
                return
            
            # AI行動実行（修正：正しいメソッド名を使用）
            ai_messages = self.ai_controller.execute_ai_turn()
            
            # AI行動結果を表示（修正：文字列リストとして処理）
            if ai_messages:
                self.dialog_manager.show_game_message("相手の行動", "\n".join(ai_messages))
            
            # AIターン終了処理
            self.game_controller.end_turn("opponent")
            
            # プレイヤーのターンに戻す
            self.game_state.current_player = "player"
            self.game_state.turn_count += 1
            self.ai_turn_in_progress = False
            
            # プレイヤーターン開始処理
            turn_messages, can_continue = self.game_controller.start_turn("player")
            if not can_continue:
                # 山札切れによる敗北
                message_text = "\n".join(turn_messages)
                self.dialog_manager.show_game_message("ゲーム終了", message_text)
                self._handle_game_over("opponent")  # プレイヤーが負け
                return
            elif turn_messages:
                message_text = "\n".join(turn_messages)
                self.dialog_manager.show_game_message("ターン開始", message_text)
            
            self.status_label.config(text="あなたのターンです")
            
            # 画面更新
            self._update_display()
            
            print("🎮 プレイヤーのターン開始")
        
        except Exception as e:
            print(f"AIターン実行エラー: {e}")
            self.ai_turn_in_progress = False
            self.game_state.current_player = "player"
            self.status_label.config(text="エラーが発生しました - あなたのターンです")
            self.dialog_manager.show_game_message("エラー", f"AI行動中にエラーが発生しました: {e}")
    
    def _handle_game_over(self, winner: str):
        """ゲーム終了処理"""
        try:
            if winner == "player":
                message = "🎉 勝利！おめでとうございます！"
            else:
                message = "😞 敗北...もう一度挑戦してください。"
            
            self.status_label.config(text=f"ゲーム終了 - {message}")
            self.dialog_manager.show_game_message("ゲーム終了", message)
        
        except Exception as e:
            print(f"ゲーム終了処理エラー: {e}")
    
    def _update_display(self):
        """表示を更新（スタジアム更新追加）"""
        try:
            # 既存の更新処理
            if self.battle_field_ui:
                self.battle_field_ui.update_display()
            
            if self.hand_ui:
                self.hand_ui.update_display()
                
            # 🆕 スタジアム情報をステータスラベルに表示
            self._update_status_with_stadium_info()
            
        except Exception as e:
            print(f"表示更新エラー: {e}")

    def _update_status_with_stadium_info(self):
        """🆕 ステータス表示にスタジアム情報を含める"""
        try:
            # 基本のステータステキストを取得
            base_status = self._get_basic_status_text()
            
            # スタジアム情報を追加
            stadium_info = ""
            if hasattr(self.game_state, 'stadium') and self.game_state.stadium:
                stadium_name = self.game_state.stadium.name
                stadium_info = f" | スタジアム: {stadium_name}"
            
            # ステータスラベルを更新
            full_status = base_status + stadium_info
            self.status_label.config(text=full_status)
            
        except Exception as e:
            print(f"ステータス更新エラー: {e}")

    def _get_basic_status_text(self) -> str:
        """基本的なステータステキストを取得"""
        if not hasattr(self, 'game_state') or not self.game_state:
            return "ゲーム未開始"
        
        if self.waiting_for_initial_setup:
            return "初期ポケモンを配置してください"
        
        if hasattr(self.game_state, 'current_player'):
            current_player = "あなた" if self.game_state.current_player == "player" else "相手"
            turn_count = getattr(self.game_state, 'turn_count', 0)
            return f"ターン {turn_count}: {current_player}のターン"
        
        return "ゲーム進行中"