# gui/game_controller.py
# Version: 4.29
# Updated: 2025-06-12 12:10
# ゲームコントローラー：公式ルール準拠ドロー処理・山札切れ敗北対応版

import random
import copy
from typing import List, Optional, Tuple

from models.game_state import GameState
from models.card import Card, CardType

class GameController:
    """ゲーム進行を制御するクラス（公式ルール準拠ドロー処理・山札切れ敗北対応版）"""
    
    def __init__(self, game_state: GameState, database_manager, debug_mode: bool = True):
        self.game_state = game_state
        self.database_manager = database_manager
        self.debug_mode = debug_mode
    
    def set_dialog_manager(self, dialog_manager):
        """ダイアログマネージャーを設定"""
        self.dialog_manager = dialog_manager
        print("ダイアログマネージャーが設定されました")

    def initialize_game(self, player_deck_id: int, opponent_deck_id: int) -> bool:
        """ゲームを初期化"""
        try:
            print(f"=== ゲーム初期化開始 ===")
            print(f"プレイヤーデッキID: {player_deck_id}, 相手デッキID: {opponent_deck_id}")
            
            # デッキIDを保存
            self.game_state.player_deck_id = player_deck_id
            self.game_state.opponent_deck_id = opponent_deck_id
            
            # デッキをロード（修正：tuple形式データの適切な処理）
            player_cards = self._load_deck_cards(player_deck_id)
            opponent_cards = self._load_deck_cards(opponent_deck_id)
            
            if not player_cards or not opponent_cards:
                print("デッキの読み込みに失敗しました")
                return False
            
            # デッキをシャッフル
            random.shuffle(player_cards)
            random.shuffle(opponent_cards)
            
            # ゲーム状態を初期化
            self.game_state.player_deck = player_cards.copy()
            self.game_state.opponent_deck = opponent_cards.copy()
            
            # サイド（プライズ）カードを配る（6枚）
            self.game_state.player_prizes = []
            self.game_state.opponent_prizes = []
            
            for _ in range(6):
                if self.game_state.player_deck:
                    self.game_state.player_prizes.append(self.game_state.player_deck.pop(0))
                if self.game_state.opponent_deck:
                    self.game_state.opponent_prizes.append(self.game_state.opponent_deck.pop(0))
            
            # マリガン処理を含む初期手札配布 - 修正：追加
            mulligan_success = self._initial_hand_with_mulligan()
            if not mulligan_success:
                print("マリガン処理に失敗しました")
                return False
            
            if self.debug_mode:
                print(f"プレイヤー手札: {len(self.game_state.player_hand)}枚")
                print(f"相手手札: {len(self.game_state.opponent_hand)}枚")
                print(f"プレイヤーデッキ残り: {len(self.game_state.player_deck)}枚")
                print(f"相手デッキ残り: {len(self.game_state.opponent_deck)}枚")
                print(f"プレイヤーサイド: {len(self.game_state.player_prizes)}枚")
                print(f"相手サイド: {len(self.game_state.opponent_prizes)}枚")
                print(f"プレイヤーマリガン回数: {self.game_state.player_mulligans}回")
                print(f"相手マリガン回数: {self.game_state.opponent_mulligans}回")
                
                # HP引き継ぎバグ修正確認（デバッグ出力）
                self._debug_card_instances()
            
            print(f"=== ゲーム初期化完了 ===")
            return True
            
        except Exception as e:
            print(f"ゲーム初期化エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _initial_hand_with_mulligan(self) -> bool:
        """マリガン処理を含む初期手札配布（マリガンペナルティ選択制対応版）"""
        try:
            print("=== 初期手札配布・マリガン処理開始 ===")
            
            # プレイヤーと相手のマリガン回数を初期化
            player_mulligans = 0
            opponent_mulligans = 0
            
            # プレイヤーの初期手札配布・マリガン処理
            player_basic_found = False
            while not player_basic_found and player_mulligans < 10:  # 無限ループ防止
                # 手札を7枚引く
                self.game_state.player_hand = []
                for _ in range(7):
                    if self.game_state.player_deck:
                        self.game_state.player_hand.append(self.game_state.player_deck.pop(0))
                
                # たねポケモンがあるかチェック - 修正：判定条件統一
                basic_pokemon = [card for card in self.game_state.player_hand 
                            if card.card_type == CardType.POKEMON and getattr(card, 'evolve_step', 0) == 0]
                
                if basic_pokemon:
                    player_basic_found = True
                    print(f"プレイヤー: たねポケモン発見 ({len(basic_pokemon)}匹)")
                else:
                    # マリガン実行
                    player_mulligans += 1
                    print(f"プレイヤー: マリガン{player_mulligans}回目（たねポケモンなし）")
                    
                    # 手札を山札に戻してシャッフル
                    self.game_state.player_deck.extend(self.game_state.player_hand)
                    random.shuffle(self.game_state.player_deck)
                    self.game_state.player_hand = []
            
            # 相手の初期手札配布・マリガン処理
            opponent_basic_found = False
            while not opponent_basic_found and opponent_mulligans < 10:  # 無限ループ防止
                # 手札を7枚引く
                self.game_state.opponent_hand = []
                for _ in range(7):
                    if self.game_state.opponent_deck:
                        self.game_state.opponent_hand.append(self.game_state.opponent_deck.pop(0))
                
                # たねポケモンがあるかチェック - 修正：判定条件統一
                basic_pokemon = [card for card in self.game_state.opponent_hand 
                            if card.card_type == CardType.POKEMON and getattr(card, 'evolve_step', 0) == 0]
                
                if basic_pokemon:
                    opponent_basic_found = True
                    print(f"相手: たねポケモン発見 ({len(basic_pokemon)}匹)")
                else:
                    # マリガン実行
                    opponent_mulligans += 1
                    print(f"相手: マリガン{opponent_mulligans}回目（たねポケモンなし）")
                    
                    # 手札を山札に戻してシャッフル
                    self.game_state.opponent_deck.extend(self.game_state.opponent_hand)
                    random.shuffle(self.game_state.opponent_deck)
                    self.game_state.opponent_hand = []
            
            # 🆕 マリガンペナルティの適用（選択制・公式ルール準拠版）
            net_player_advantage = opponent_mulligans - player_mulligans
            net_opponent_advantage = player_mulligans - opponent_mulligans
            
            # プレイヤーが追加ドローを受ける権利がある場合
            if net_player_advantage > 0:
                print(f"プレイヤーがマリガンペナルティで最大{net_player_advantage}枚引く権利を獲得")
                # 追加ドローは後でUIで選択するため、ここでは何もしない
                
            # 相手（AI）が追加ドローを受ける権利がある場合
            elif net_opponent_advantage > 0:
                # AIの判断ロジック：戦略的に決定
                ai_draw_count = self._ai_decide_mulligan_penalty_draw(net_opponent_advantage)
                
                for _ in range(ai_draw_count):
                    if self.game_state.opponent_deck:
                        self.game_state.opponent_hand.append(self.game_state.opponent_deck.pop(0))
                
                if ai_draw_count > 0:
                    print(f"相手がマリガンペナルティで{ai_draw_count}枚追加ドロー（最大{net_opponent_advantage}枚）")
                else:
                    print(f"相手はマリガンペナルティの追加ドローを辞退")

            # マリガン回数を記録
            self.game_state.player_mulligans = player_mulligans
            self.game_state.opponent_mulligans = opponent_mulligans
            
            print(f"マリガン処理完了: プレイヤー{player_mulligans}回, 相手{opponent_mulligans}回")
            print("=== 初期手札配布・マリガン処理完了 ===")
            
            return player_basic_found and opponent_basic_found
            
        except Exception as e:
            print(f"マリガン処理エラー: {e}")
            return False
    
    def _ai_decide_mulligan_penalty_draw(self, max_draw: int) -> int:
        """
        AIがマリガンペナルティで何枚引くかを戦略的に決定
        Args:
            max_draw:最大ドロー可能枚数
            Returns:実際に引く枚数（0〜max_draw）
        """
        try:
            # 基本的な判断ロジック：手札の質を考慮
            current_hand_size = len(self.game_state.opponent_hand)
            
            # 手札が少ない場合は多めに引く
            if current_hand_size <= 5:
                return max_draw  # 最大まで引く
            
            # 手札に十分なたねポケモンがある場合は控えめに
            basic_pokemon_count = len([card for card in self.game_state.opponent_hand 
                                     if card.card_type == CardType.POKEMON and getattr(card, 'evolve_step', 0) == 0])
            
            if basic_pokemon_count >= 3:
                return max(0, max_draw - 1)  # 1枚少なく引く
            
            # その他の場合は中程度
            return min(max_draw, max(1, max_draw // 2))
            
        except Exception as e:
            print(f"AI マリガンペナルティ判断エラー: {e}")
            return max_draw  # エラー時は最大まで引く

    def execute_additional_draw(self, draw_count: int) -> bool:
        """
        マリガンペナルティによる追加ドローを実行
        Args:
            draw_count: 追加でドローする枚数
        Returns: 成功した場合True
        """
        try:
            if draw_count <= 0:
                return True
            
            # 追加ドロー可能枚数をチェック
            max_additional = max(0, self.game_state.opponent_mulligans - self.game_state.player_mulligans)
            if draw_count > max_additional:
                print(f"追加ドロー枚数が上限を超えています: {draw_count} > {max_additional}")
                return False
            
            # 指定された枚数をドロー
            drawn_cards = []
            for _ in range(draw_count):
                if self.game_state.player_deck:
                    card = self.game_state.player_deck.pop(0)
                    self.game_state.player_hand.append(card)
                    drawn_cards.append(card)
                else:
                    print("山札が不足しています")
                    break
            
            print(f"マリガンペナルティで{len(drawn_cards)}枚追加ドロー")
            if self.debug_mode:
                card_names = [card.name for card in drawn_cards]
                print(f"追加ドローしたカード: {card_names}")
            
            return True
            
        except Exception as e:
            print(f"追加ドロー実行エラー: {e}")
            return False

    def _load_deck_cards(self, deck_id: int) -> List[Card]:
        """
        デッキIDからカードリストを取得（tuple形式データ修正版）
        
        重要：DatabaseManagerは(Card, int)のtupleリストを返すため、
        適切に分解して各カードの枚数分のコピーを作成します。
        """
        try:
            # DatabaseManagerから(Card, int)のtupleリストを取得
            deck_data = self.database_manager.get_deck_cards(deck_id)
            
            if not deck_data:
                print(f"デッキID {deck_id} のカードが見つかりません")
                return []
            
            cards = []
            instance_counter = 0
            
            for card_tuple in deck_data:
                try:
                    # tupleから適切にCardオブジェクトと枚数を取り出し
                    if isinstance(card_tuple, tuple) and len(card_tuple) == 2:
                        original_card, count = card_tuple
                        print(f"デッキ{deck_id}: {original_card.name} x {count}枚")
                        
                        # 指定された枚数分だけカードのコピーを作成
                        for i in range(count):
                            # 各カードの独立したコピーを作成（重要：deep copyによる完全な独立性確保）
                            card_copy = copy.deepcopy(original_card)
                            
                            # HP引き継ぎバグ修正：各インスタンスにユニークIDを付与
                            card_copy._instance_id = f"{card_copy.name}_{instance_counter}_{id(card_copy)}"
                            
                            # ダメージ状態を確実に初期化
                            card_copy.damage_taken = 0
                            if hasattr(card_copy, 'special_conditions'):
                                card_copy.special_conditions = set()
                            
                            # ターンフラグも初期化
                            if hasattr(card_copy, 'summoned_this_turn'):
                                card_copy.summoned_this_turn = False
                            if hasattr(card_copy, 'evolved_this_turn'):
                                card_copy.evolved_this_turn = False
                            
                            cards.append(card_copy)
                            instance_counter += 1
                            
                            if self.debug_mode and i == 0:  # 最初の1枚だけログ出力
                                print(f"  カード作成: {card_copy.name} (インスタンス: {card_copy._instance_id})")
                    else:
                        print(f"警告: 不正なデータ形式 - {card_tuple}")
                        
                except Exception as e:
                    print(f"カードコピー作成エラー {card_tuple}: {e}")
                    continue
            
            print(f"デッキ{deck_id}の読み込み完了: {len(cards)}枚")
            return cards
            
        except Exception as e:
            print(f"デッキ読み込みエラー (ID: {deck_id}): {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _debug_card_instances(self):
        """カードインスタンスの独立性をデバッグ確認"""
        try:
            print("\n=== カードインスタンス独立性チェック ===")
            
            # 全カードを収集
            all_cards = []
            all_cards.extend(self.game_state.player_hand)
            all_cards.extend(self.game_state.opponent_hand)
            all_cards.extend(self.game_state.player_deck)
            all_cards.extend(self.game_state.opponent_deck)
            all_cards.extend(self.game_state.player_prizes)
            all_cards.extend(self.game_state.opponent_prizes)
            all_cards.extend(self.game_state.player_discard)
            all_cards.extend(self.game_state.opponent_discard)
            
            if self.game_state.player_active:
                all_cards.append(self.game_state.player_active)
            
            if self.game_state.opponent_active:
                all_cards.append(self.game_state.opponent_active)
            
            for pokemon in self.game_state.player_bench + self.game_state.opponent_bench:
                if pokemon:
                    all_cards.append(pokemon)
            
            # 同名カードのインスタンス独立性をチェック
            name_instances = {}
            for card in all_cards:
                name = card.name
                instance_id = getattr(card, '_instance_id', id(card))
                
                if name not in name_instances:
                    name_instances[name] = []
                
                name_instances[name].append({
                    'instance_id': instance_id,
                    'damage': card.damage_taken,
                    'object_id': id(card)
                })
            
            # 検証結果出力
            issues_found = False
            for name, instances in name_instances.items():
                if len(instances) > 1:
                    print(f"\n{name}のインスタンス数: {len(instances)}")
                    for i, instance in enumerate(instances):
                        print(f"  インスタンス{i+1}: ID={instance['instance_id']}, ダメージ={instance['damage']}, オブジェクトID={instance['object_id']}")
                    
                    # 同じオブジェクトIDがあるかチェック
                    object_ids = [inst['object_id'] for inst in instances]
                    if len(set(object_ids)) != len(object_ids):
                        print(f"  ⚠️ 警告: {name}で同じオブジェクトインスタンスが複数存在します！")
                        issues_found = True
            
            if not issues_found:
                print("✅ カードインスタンスの独立性に問題はありません")
                
            return not issues_found
            
        except Exception as e:
            print(f"インスタンス検証エラー: {e}")
            return False
    
    
    def setup_initial_pokemon(self, player: str) -> bool:
        """初期ポケモンの配置（v4.30修正版：ポケモン以外配置防止）"""
        try:
            print(f"=== {player}の初期ポケモン配置開始 ===")
            
            # 手札を取得
            if player == "player":
                hand = self.game_state.player_hand
            else:
                hand = self.game_state.opponent_hand
            
            # たねポケモンを探す（ポケモンカードのみ）
            basic_pokemon = [card for card in hand if self._is_basic_pokemon(card)]
            
            if not basic_pokemon:
                print(f"{player}の手札にたねポケモンがありません")
                # マリガン処理は_initial_hand_with_mulliganで実行済み
                return False
            
            if self.debug_mode:
                pokemon_names = [p.name for p in basic_pokemon]
                print(f"{player}のたねポケモン: {pokemon_names}")
            
            # 最初のたねポケモンをバトル場に配置
            active_pokemon = basic_pokemon[0]
            
            # 手札から取り除いてバトル場に配置
            hand.remove(active_pokemon)
            
            if player == "player":
                self.game_state.player_active = active_pokemon
            else:
                self.game_state.opponent_active = active_pokemon
            
            # 重要：初期配置時はsummoned_this_turnフラグをFalseに設定
            # （初期配置は「そのターンに出された」扱いにしない）
            active_pokemon.summoned_this_turn = False
            self.game_state.set_pokemon_summoned_this_turn(active_pokemon, False)
            
            print(f"{player}のバトル場: {active_pokemon.name}")
            
            # 残りのたねポケモンをベンチに配置（最大5匹）
            bench_pokemon = basic_pokemon[1:6]  # 最大5匹まで
            
            if player == "player":
                for i, pokemon in enumerate(bench_pokemon):
                    if i < 5:  # ベンチは最大5匹
                        hand.remove(pokemon)
                        self.game_state.player_bench[i] = pokemon
                        
                        # 初期配置時はsummoned_this_turnフラグをFalseに設定
                        pokemon.summoned_this_turn = False
                        self.game_state.set_pokemon_summoned_this_turn(pokemon, False)
                        
                        print(f"{player}のベンチ{i+1}: {pokemon.name}")
            else:
                for i, pokemon in enumerate(bench_pokemon):
                    if i < 5:  # ベンチは最大5匹
                        hand.remove(pokemon)
                        self.game_state.opponent_bench[i] = pokemon
                        
                        # 初期配置時はsummoned_this_turnフラグをFalseに設定
                        pokemon.summoned_this_turn = False
                        self.game_state.set_pokemon_summoned_this_turn(pokemon, False)
                        
                        print(f"{player}のベンチ{i+1}: {pokemon.name}")
            
            print(f"=== {player}の初期ポケモン配置完了 ===")
            return True
            
        except Exception as e:
            print(f"{player}の初期ポケモン配置エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _is_basic_pokemon(self, card: Card) -> bool:
        """基本ポケモン（たねポケモン）かどうかをチェック（修正版）"""
        return (card.card_type == CardType.POKEMON and 
                getattr(card, 'evolve_step', 0) == 0)
    
    def start_turn(self, player: str) -> Tuple[List[str], bool]:
        """
        ターン開始処理（v4.29ドロー処理統合版・山札切れ敗北対応）
        
        Returns:
            Tuple[List[str], bool]: (メッセージリスト, ゲーム継続可能か)
        """
        try:
            print(f"=== {player}のターン開始 ===")
            messages = []
            
            # ゲーム状態でターン開始処理
            self.game_state.start_turn(player)
            
            # 🆕 ドロー処理（v4.29修正版：公式ルール準拠）
            if self.game_state.can_draw_card():
                drawn_card, can_continue = self.game_state.draw_card(player)
                
                if not can_continue:
                    # 🆕 山札切れによる敗北
                    messages.append(f"{player}は山札が空のためカードを引けませんでした")
                    messages.append(f"{player}の敗北です")
                    print(f"🏁 ゲーム終了: {player}が山札切れで敗北")
                    return messages, False  # ゲーム終了
                elif drawn_card:
                    messages.append(f"{player}が{drawn_card.name}を引きました")
                    print(f"✅ ドロー成功: {player}が{drawn_card.name}を引きました")
                else:
                    messages.append(f"{player}はドローに失敗しました")
                    print(f"⚠️ ドロー失敗: {player}")
            else:
                print("ℹ️ ドロー条件を満たしていません")
            
            # ターン開始時の特殊状態処理
            special_messages = self._process_special_conditions_start_of_turn(player)
            messages.extend(special_messages)
            
            print(f"=== {player}のターン開始処理完了 ===")
            return messages, True  # ゲーム継続
            
        except Exception as e:
            print(f"ターン開始処理エラー ({player}): {e}")
            return [f"ターン開始処理でエラーが発生しました: {e}"], True
    
    def end_turn(self, player: str):
        """ターン終了処理（v4.28修正版）"""
        try:
            current_player = self.game_state.current_player
            print(f"=== {current_player}のターン終了処理開始 ===")
            
            # ターン終了時の特殊状態処理
            self._process_special_conditions_end_of_turn(current_player)
            
            # ゲーム状態でターン終了処理
            self.game_state.switch_turn()
            
            print(f"=== {current_player}のターン終了処理完了 ===")
            
        except Exception as e:
            print(f"ターン終了処理エラー: {e}")
            import traceback
            traceback.print_exc()
            
    def _process_special_conditions_start_of_turn(self, player: str) -> List[str]:
        """ターン開始時の特殊状態処理"""
        messages = []
        try:
            # プレイヤーのアクティブポケモンを取得
            if player == "player":
                active_pokemon = self.game_state.player_active
            else:
                active_pokemon = self.game_state.opponent_active
            
            if not active_pokemon or not hasattr(active_pokemon, 'special_conditions'):
                return messages
            
            # 特殊状態の処理（基本実装）
            from models.card import SpecialCondition
            
            conditions_to_remove = set()
            
            # どく、やけどのダメージ処理
            if SpecialCondition.POISON in active_pokemon.special_conditions:
                active_pokemon.damage_taken += 10
                messages.append(f"{active_pokemon.name}はどくのダメージを受けました（10ダメージ）")
                print(f"{active_pokemon.name}はどくのダメージを受けました（10ダメージ）")
                
            if SpecialCondition.BURN in active_pokemon.special_conditions:
                active_pokemon.damage_taken += 20
                messages.append(f"{active_pokemon.name}はやけどのダメージを受けました（20ダメージ）")
                print(f"{active_pokemon.name}はやけどのダメージを受けました（20ダメージ）")
                # やけどは自動的に回復
                conditions_to_remove.add(SpecialCondition.BURN)
            
            # ねむり、マヒの自動回復判定（簡易実装）
            if SpecialCondition.SLEEP in active_pokemon.special_conditions:
                # 50%の確率で回復
                if random.random() < 0.5:
                    conditions_to_remove.add(SpecialCondition.SLEEP)
                    messages.append(f"{active_pokemon.name}のねむりが回復しました")
                    print(f"{active_pokemon.name}のねむりが回復しました")
            
            if SpecialCondition.PARALYSIS in active_pokemon.special_conditions:
                # マヒは自動的に回復
                conditions_to_remove.add(SpecialCondition.PARALYSIS)
                messages.append(f"{active_pokemon.name}のマヒが回復しました")
                print(f"{active_pokemon.name}のマヒが回復しました")
            
            # 特殊状態を削除
            for condition in conditions_to_remove:
                active_pokemon.special_conditions.discard(condition)
            
            return messages
                
        except Exception as e:
            print(f"ターン開始時特殊状態処理エラー: {e}")
            return [f"特殊状態処理でエラーが発生しました: {e}"]
    
    def _process_special_conditions_end_of_turn(self, player: str):
        """ターン終了時の特殊状態処理"""
        try:
            # 基本実装では何もしない
            # 将来的にターン終了時に発動する効果があれば実装
            pass
            
        except Exception as e:
            print(f"ターン終了時特殊状態処理エラー: {e}")