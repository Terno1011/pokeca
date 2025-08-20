# models/game_state.py
# Version: 4.24
# Updated: 2025-06-12 12:10
# 公式ルール準拠ドロー処理・山札切れ敗北対応版

from typing import List, Optional, Tuple
from .card import Card

class GameState:
    """ゲーム状態を管理するクラス（公式ルール準拠ドロー処理・山札切れ敗北対応版）"""
    
    def __init__(self):
        # 手札
        self.player_hand: List[Card] = []
        self.opponent_hand: List[Card] = []
        
        # ベンチ（5匹まで）
        self.player_bench: List[Optional[Card]] = [None] * 5
        self.opponent_bench: List[Optional[Card]] = [None] * 5
        
        # バトル場
        self.player_active: Optional[Card] = None
        self.opponent_active: Optional[Card] = None
        
        # プライズカード
        self.player_prizes: List[Card] = []
        self.opponent_prizes: List[Card] = []
        
        # デッキ
        self.player_deck: List[Card] = []
        self.opponent_deck: List[Card] = []
        
        # 捨て札
        self.player_discard: List[Card] = []
        self.opponent_discard: List[Card] = []
        
        # ゲーム状態
        self.turn_count: int = 0
        self.current_player: str = "player"  # "player" or "opponent"
        
        # 🆕 先攻プレイヤー管理（v4.23追加）
        self.first_player: Optional[str] = None  # 最初にターンを開始するプレイヤー
        self.first_turn_player: Optional[str] = None  # 互換性のため
        
        # ターン制限
        self.energy_played_this_turn: bool = False
        self.supporter_played_this_turn: bool = False
        
        # 🆕 攻撃フラグ管理強化（v4.23追加）
        self.player_has_attacked: bool = False
        self.opponent_has_attacked: bool = False
        
        # マリガン管理
        self.player_mulligans: int = 0
        self.opponent_mulligans: int = 0
        
        # 🆕 マリガンペナルティ管理（追加）
        self.pending_player_mulligan_draw: int = 0
        self.pending_opponent_mulligan_draw: int = 0
        
        # v4.23強化：進化制限管理の修正
        self.initialization_complete: bool = False
        self.player_first_turn_completed: bool = False
        self.opponent_first_turn_completed: bool = False
        
        # デッキID管理
        self.player_deck_id: Optional[int] = None
        self.opponent_deck_id: Optional[int] = None
        
        # スタジアム
        self.stadium: Optional[Card] = None
        
        # ターン詳細状態
        self.turn_phase: str = "main"
        self.attacks_this_turn: int = 0
        self.max_attacks_per_turn: int = 1
        self.turn_started_at: Optional[str] = None
        self.last_action: str = ""

    def can_use_supporter(self) -> bool:
        """サポートカードが使用可能かチェック（公式ルール準拠版）"""
        # 1. 1ターン1枚制限チェック
        if self.supporter_played_this_turn:
            return False
        
        # 🆕 2. 先攻最初のターン制限チェック（公式ルール準拠）
        if self.is_first_player_first_turn():
            return False
        
        return True

    def get_supporter_restriction_reason(self) -> str:
        """サポート使用制限の理由を取得"""
        if self.supporter_played_this_turn:
            return "サポートは1ターンに1枚までです"
        
        if self.is_first_player_first_turn():
            return "先攻プレイヤーの最初のターンはサポートを使用できません"
        
        return ""

    def can_attach_energy(self) -> bool:
        """エネルギーが装着可能かチェック"""
        return not self.energy_played_this_turn
    
    def can_attack(self) -> bool:
        """攻撃が可能かチェック（v4.23強化版）"""
        # 基本的な攻撃回数制限
        if self.attacks_this_turn >= self.max_attacks_per_turn:
            return False
        
        # プレイヤー別の攻撃済みフラグチェック
        if self.current_player == "player" and self.player_has_attacked:
            return False
        elif self.current_player == "opponent" and self.opponent_has_attacked:
            return False
        
        # 🆕 先攻1ターン目の攻撃制限チェック
        if self.is_first_player_first_turn():
            return False
        
        return True
    
    def is_first_player_first_turn(self) -> bool:
        """先攻プレイヤーの最初のターンかどうかを判定（v4.23新規）"""
        try:
            return (
                self.turn_count == 1 and 
                self.current_player == self.first_player and
                self.first_player is not None
            )
        except Exception as e:
            print(f"先攻1ターン目判定エラー: {e}")
            return False
    
    def can_draw_card(self) -> bool:
        """カードを引けるかどうかを判定（v4.24修正版）"""
        try:
            # 初期化が完了していない場合は引けない
            if not self.initialization_complete:
                return False
            
            # 公式ルール：先攻1ターン目でもドローする（攻撃制限のみ）
            return True
        except Exception as e:
            print(f"ドロー可能性判定エラー: {e}")
            return False
    
    def draw_card(self, player: str) -> Tuple[Optional[Card], bool]:
        """
        指定プレイヤーがカードを1枚引く（v4.24修正版）
        
        Returns:
            Tuple[Optional[Card], bool]: (引いたカード, ゲーム継続可能か)
            ゲーム継続不可の場合、そのプレイヤーは敗北
        """
        try:
            if player == "player":
                deck = self.player_deck
                hand = self.player_hand
            elif player == "opponent":
                deck = self.opponent_deck
                hand = self.opponent_hand
            else:
                print(f"無効なプレイヤー指定: {player}")
                return None, True
            
            # 🆕 公式ルール：山札が空の場合は即敗北
            if not deck:
                print(f"⚠️ {player}の山札が空です - ゲーム終了（敗北）")
                return None, False  # ゲーム継続不可
            
            # カードを1枚引く
            drawn_card = deck.pop(0)
            hand.append(drawn_card)
            
            print(f"{player}が{drawn_card.name}を引きました")
            return drawn_card, True  # ゲーム継続可能
            
        except Exception as e:
            print(f"カードドローエラー ({player}): {e}")
            return None, True
    
    def is_current_player_first_turn(self) -> bool:
        """現在のプレイヤーの最初のターンかどうかを判定"""
        if self.current_player == "player":
            return not self.player_first_turn_completed
        else:
            return not self.opponent_first_turn_completed
    
    def set_first_player(self, player: str):
        """先攻プレイヤーを設定（v4.23新規）"""
        self.first_player = player
        self.first_turn_player = player  # 互換性のため
        print(f"先攻プレイヤー設定: {player}")
    
    def mark_attack_completed(self):
        """攻撃完了をマーク（v4.23強化版）"""
        self.attacks_this_turn += 1
        
        if self.current_player == "player":
            self.player_has_attacked = True
        else:
            self.opponent_has_attacked = True
        
        print(f"攻撃完了マーク: {self.current_player} (攻撃回数: {self.attacks_this_turn})")
    
    def can_evolve_pokemon(self, pokemon: Card) -> bool:
        """ポケモンが進化可能かチェック（v4.23修正版）"""
        if not pokemon or not self.initialization_complete:
            return False
        
        # 1. 最初の自分の番では全てのポケモンが進化できない
        if self.current_player == "player" and not self.player_first_turn_completed:
            print(f"進化制限: プレイヤーの最初のターンのため進化不可")
            return False
        elif self.current_player == "opponent" and not self.opponent_first_turn_completed:
            print(f"進化制限: 相手の最初のターンのため進化不可")
            return False
        
        # 2. そのポケモンがこのターンに場に出されたかチェック
        summoned_this_turn = getattr(pokemon, 'summoned_this_turn', False)
        if summoned_this_turn:
            print(f"進化制限: {pokemon.name}はこのターンに場に出されたため進化不可")
            return False
        
        print(f"進化可能: {pokemon.name}")
        return True
    
    def reset_turn_flags(self):
        """ターン開始時のフラグリセット（v4.23強化版）"""
        print(f"=== ターンフラグリセット開始 ===")
        
        # 基本的なフラグリセット
        self.energy_played_this_turn = False
        self.supporter_played_this_turn = False
        self.attacks_this_turn = 0
        
        # 攻撃フラグリセット
        if self.current_player == "player":
            self.player_has_attacked = False
            print("プレイヤーの攻撃フラグをリセット")
        else:
            self.opponent_has_attacked = False
            print("相手の攻撃フラグをリセット")
        
        # summoned_this_turnフラグリセット（現在のプレイヤーのみ）
        self._reset_summoned_flags_enhanced(self.current_player)
        
        print(f"=== ターンフラグリセット完了 ===")
    
    def _reset_summoned_flags_enhanced(self, player: str):
        """指定プレイヤーのsummoned_this_turnフラグを強制リセット（v4.23修正版）"""
        try:
            print(f"--- {player}のsummoned_this_turnフラグリセット開始 ---")
            
            if player == "player":
                # バトル場のポケモン
                if self.player_active:
                    old_flag = getattr(self.player_active, 'summoned_this_turn', False)
                    self.player_active.summoned_this_turn = False
                    print(f"プレイヤーバトル場 {self.player_active.name}: {old_flag} → False")
                
                # ベンチのポケモン
                for i, pokemon in enumerate(self.player_bench):
                    if pokemon:
                        old_flag = getattr(pokemon, 'summoned_this_turn', False)
                        pokemon.summoned_this_turn = False
                        print(f"プレイヤーベンチ{i} {pokemon.name}: {old_flag} → False")
            
            else:  # opponent
                # バトル場のポケモン
                if self.opponent_active:
                    old_flag = getattr(self.opponent_active, 'summoned_this_turn', False)
                    self.opponent_active.summoned_this_turn = False
                    print(f"相手バトル場 {self.opponent_active.name}: {old_flag} → False")
                
                # ベンチのポケモン
                for i, pokemon in enumerate(self.opponent_bench):
                    if pokemon:
                        old_flag = getattr(pokemon, 'summoned_this_turn', False)
                        pokemon.summoned_this_turn = False
                        print(f"相手ベンチ{i} {pokemon.name}: {old_flag} → False")
        
        except Exception as e:
            print(f"フラグリセットエラー ({player}): {e}")
        
        print(f"--- {player}のsummoned_this_turnフラグリセット完了 ---")
    
    def switch_turn(self):
        """ターンを交代（v4.24強化版：ドロー処理統合）"""
        print(f"=== ターン交代処理開始 ===")
        print(f"現在: ターン{self.turn_count}, {self.current_player}")
        
        # 現在のプレイヤーの最初のターン完了をマーク
        if self.current_player == "player" and not self.player_first_turn_completed:
            self.player_first_turn_completed = True
            print("プレイヤーの最初のターンが完了しました")
        elif self.current_player == "opponent" and not self.opponent_first_turn_completed:
            self.opponent_first_turn_completed = True
            print("相手の最初のターンが完了しました")
        
        # ターン交代
        old_player = self.current_player
        self.current_player = "opponent" if self.current_player == "player" else "player"
        self.turn_count += 1
        
        # 新しいターンのフラグリセット
        self.reset_turn_flags()
        
        print(f"ターン交代完了: {old_player} → {self.current_player}")
        print(f"新ターン: ターン{self.turn_count}, {self.current_player}")
        
        # 先攻1ターン目チェック情報表示
        if self.is_first_player_first_turn():
            print(f"⚠️  先攻1ターン目: {self.current_player}は攻撃できません")
        
        # デバッグ情報
        if self.current_player == "player":
            can_evolve = not self.is_current_player_first_turn()
            print(f"プレイヤーの進化可能状態: {can_evolve}")
        else:
            can_evolve = not self.is_current_player_first_turn()
            print(f"相手の進化可能状態: {can_evolve}")
        
        print(f"=== ターン交代処理完了 ===")
    
    def start_turn(self, player: str):
        """ターン開始処理（v4.24追加）"""
        print(f"=== {player}のターン開始処理 ===")
        
        # 念のため、ターン開始時にもフラグ状態を確認
        self._debug_summoned_flags()
        
        # 先攻1ターン目の場合は警告表示
        if self.is_first_player_first_turn():
            print(f"⚠️  先攻1ターン目: 攻撃制限が有効です")
        
        print(f"=== {player}のターン開始処理完了 ===")
    
    def _debug_summoned_flags(self):
        """デバッグ用：現在のsummoned_this_turnフラグ状態を表示"""
        print("--- 現在のsummoned_this_turnフラグ状態 ---")
        
        # プレイヤー
        if self.player_active:
            flag = getattr(self.player_active, 'summoned_this_turn', False)
            print(f"プレイヤーバトル場 {self.player_active.name}: {flag}")
        
        for i, pokemon in enumerate(self.player_bench):
            if pokemon:
                flag = getattr(pokemon, 'summoned_this_turn', False)
                print(f"プレイヤーベンチ{i} {pokemon.name}: {flag}")
        
        # 相手
        if self.opponent_active:
            flag = getattr(self.opponent_active, 'summoned_this_turn', False)
            print(f"相手バトル場 {self.opponent_active.name}: {flag}")
        
        for i, pokemon in enumerate(self.opponent_bench):
            if pokemon:
                flag = getattr(pokemon, 'summoned_this_turn', False)
                print(f"相手ベンチ{i} {pokemon.name}: {flag}")
        
        print("--- フラグ状態表示完了 ---")
    
    def set_pokemon_summoned_this_turn(self, pokemon: Card, value: bool = True):
        """ポケモンのsummoned_this_turnフラグを設定（v4.23追加）"""
        if pokemon:
            old_value = getattr(pokemon, 'summoned_this_turn', False)
            pokemon.summoned_this_turn = value
            print(f"フラグ設定: {pokemon.name} summoned_this_turn {old_value} → {value}")
    
    def get_turn_status(self) -> dict:
        """現在のターン状態を取得（v4.23強化版）"""
        return {
            "turn_count": self.turn_count,
            "current_player": self.current_player,
            "first_player": self.first_player,
            "is_first_player_first_turn": self.is_first_player_first_turn(),
            "can_draw_card": self.can_draw_card(),  # v4.24更新：先攻でも引ける
            "energy_played": self.energy_played_this_turn,
            "supporter_played": self.supporter_played_this_turn,
            "attacks_this_turn": self.attacks_this_turn,
            "player_has_attacked": self.player_has_attacked,
            "opponent_has_attacked": self.opponent_has_attacked,
            "turn_phase": self.turn_phase,
            "player_first_turn_completed": self.player_first_turn_completed,
            "opponent_first_turn_completed": self.opponent_first_turn_completed,
            "initialization_complete": self.initialization_complete,
            "can_attack": self.can_attack()
        }
    
    def is_game_over(self) -> bool:
        """ゲーム終了判定"""
        # サイド（プライズ）がすべて取られた場合
        if len(self.player_prizes) == 0 or len(self.opponent_prizes) == 0:
            return True
        
        # バトル場にポケモンがいない場合
        if not self.player_active or not self.opponent_active:
            return True
        
        # デッキが空の場合
        if len(self.player_deck) == 0 or len(self.opponent_deck) == 0:
            return True
        
        return False
    
    def get_winner(self) -> Optional[str]:
        """勝者を取得"""
        if len(self.player_prizes) == 0:
            return "player"
        elif len(self.opponent_prizes) == 0:
            return "opponent"
        elif not self.opponent_active:
            return "player"
        elif not self.player_active:
            return "opponent"
        elif len(self.opponent_deck) == 0:
            return "player"
        elif len(self.player_deck) == 0:
            return "opponent"
        
        return None
    
    def validate_game_state(self) -> List[str]:
        """ゲーム状態の妥当性をチェック"""
        errors = []
        
        # バトル場チェック
        if not self.player_active:
            errors.append("プレイヤーのバトル場にポケモンがいません")
        if not self.opponent_active:
            errors.append("相手のバトル場にポケモンがいません")
        
        # ベンチ数チェック
        player_bench_count = sum(1 for p in self.player_bench if p is not None)
        opponent_bench_count = sum(1 for p in self.opponent_bench if p is not None)
        
        if player_bench_count > 5:
            errors.append(f"プレイヤーのベンチポケモン数が異常です: {player_bench_count}")
        if opponent_bench_count > 5:
            errors.append(f"相手のベンチポケモン数が異常です: {opponent_bench_count}")
        
        # 先攻1ターン目攻撃制限チェック
        if self.is_first_player_first_turn() and (self.player_has_attacked or self.opponent_has_attacked):
            errors.append("先攻1ターン目に攻撃が行われました（ルール違反）")
        
        return errors