# utils/energy_cost_checker.py
# Version: 2.1
# Updated: 2025-06-11 18:40
# 先攻1ターン目攻撃制限対応・無色エネルギーシステム修正版

from typing import Dict, Optional, Tuple, List
from models.card import Card

class EnergyCostChecker:
    """エネルギーコスト判定を行うクラス（先攻1ターン目攻撃制限対応・無色エネルギーシステム対応版）"""

    @staticmethod
    def can_use_attack(pokemon: Card, attack_number: int = 1, game_state=None) -> Tuple[bool, str]:
        """
        指定されたワザが使用可能かをチェック（旧形式カードデータ対応版）
        
        Args:
            pokemon: 攻撃するポケモン
            attack_number: ワザ番号（1 or 2）
            game_state: ゲーム状態（先攻1ターン目チェック用）
            
        Returns:
            Tuple[bool, str]: (使用可能か, 詳細メッセージ)
        """
        try:
            print(f"🔍 エネルギーコストチェック開始: {pokemon.name}, ワザ{attack_number}")
            
            # 先攻1ターン目の攻撃制限チェック
            if game_state and hasattr(game_state, 'is_first_player_first_turn'):
                if game_state.is_first_player_first_turn():
                    print("  ❌ 先攻1ターン目制限")
                    return False, "先攻プレイヤーの最初のターンは攻撃できません"
            
            # ワザの存在チェック（旧形式対応）
            if attack_number == 1:
                attack_name = getattr(pokemon, 'attack_name', None)
                cost_types = getattr(pokemon, 'attack_cost_types', None)
                attack_power = getattr(pokemon, 'attack_power', None)
            elif attack_number == 2:
                attack_name = getattr(pokemon, 'attack2_name', None)
                cost_types = getattr(pokemon, 'attack2_cost_types', None)
                attack_power = getattr(pokemon, 'attack2_power', None)
            else:
                print("  ❌ 無効なワザ番号")
                return False, "無効なワザ番号です"
            
            print(f"  - ワザ名: {attack_name}")
            print(f"  - コスト: {cost_types}")
            print(f"  - ダメージ: {attack_power}")
            
            if not attack_name:
                print(f"  ❌ ワザ{attack_number}が設定されていません")
                return False, f"ワザ{attack_number}は設定されていません"
            
            # コストが設定されていない場合は使用可能
            if not cost_types:
                print("  ✅ コストなしで使用可能")
                return True, f"「{attack_name}」は使用可能です（コスト：なし）"
            
            # 装着されているエネルギーの集計
            attached_energy = EnergyCostChecker._get_attached_energy_summary(pokemon)
            print(f"  - 装着エネルギー: {attached_energy}")
            
            # 無色エネルギー対応のコスト判定
            can_use, detailed_result = EnergyCostChecker._check_energy_cost_with_colorless(
                cost_types, attached_energy, attack_name, attack_power
            )
            
            print(f"  - 判定結果: {can_use}, {detailed_result}")
            return can_use, detailed_result
            
        except Exception as e:
            print(f"  ❌ エネルギーコスト判定エラー: {e}")
            return False, f"エネルギーコスト判定エラー: {e}"

    @staticmethod
    def _get_attached_energy_summary(pokemon: Card) -> Dict[str, int]:
        """ポケモンに装着されているエネルギーを集計（デバッグ強化版）"""
        energy_summary = {"total": 0}
        
        print(f"    🔍 エネルギー集計開始: {pokemon.name}")
        
        if not hasattr(pokemon, 'attached_energy'):
            print("    - attached_energy属性なし")
            return energy_summary
        
        attached_energy_list = pokemon.attached_energy
        if not attached_energy_list:
            print("    - 装着エネルギーなし")
            return energy_summary
        
        print(f"    - 装着エネルギー数: {len(attached_energy_list)}")
        
        for i, energy_card in enumerate(attached_energy_list):
            # エネルギータイプの正規化
            energy_type = getattr(energy_card, 'energy_kind', None)
            if not energy_type:
                energy_type = getattr(energy_card, 'name', '不明')
            
            print(f"    - エネルギー{i+1}: {energy_card.name}, タイプ: {energy_type}")
            
            # タイプ名の正規化
            if energy_type in ['無色エネルギー', 'colorless', 'Colorless', 'ノーマル']:
                energy_type = '無色'
            elif energy_type in ['炎エネルギー', 'fire', 'Fire', '火']:
                energy_type = '炎'
            elif energy_type in ['水エネルギー', 'water', 'Water']:
                energy_type = '水'
            elif energy_type in ['雷エネルギー', 'electric', 'Electric', '電気']:
                energy_type = '雷'
            elif energy_type in ['草エネルギー', 'grass', 'Grass']:
                energy_type = '草'
            elif energy_type in ['超エネルギー', 'psychic', 'Psychic']:
                energy_type = '超'
            elif energy_type in ['闘エネルギー', 'fighting', 'Fighting']:
                energy_type = '闘'
            elif energy_type in ['悪エネルギー', 'darkness', 'Darkness']:
                energy_type = '悪'
            elif energy_type in ['鋼エネルギー', 'metal', 'Metal']:
                energy_type = '鋼'
            elif energy_type in ['フェアリーエネルギー', 'fairy', 'Fairy']:
                energy_type = 'フェアリー'
            elif energy_type in ['ドラゴンエネルギー', 'dragon', 'Dragon']:
                energy_type = 'ドラゴン'
            
            print(f"    - 正規化後タイプ: {energy_type}")
            
            # 集計
            if energy_type not in energy_summary:
                energy_summary[energy_type] = 0
            energy_summary[energy_type] += 1
            energy_summary["total"] += 1
        
        print(f"    - 集計結果: {energy_summary}")
        return energy_summary

    @staticmethod
    def _check_energy_cost_with_colorless(cost_types: Dict[str, int], attached_energy: Dict[str, int], 
                                         attack_name: str, attack_power: Optional[int]) -> Tuple[bool, str]:
        """無色エネルギーを考慮したコスト判定（修正版）"""
        
        # 必要なエネルギーの総数
        total_required = sum(cost_types.values())
        total_attached = attached_energy.get("total", 0)
        
        # 総数が足りない場合
        if total_attached < total_required:
            missing = total_required - total_attached
            return False, f"「{attack_name}」はエネルギーが{missing}個足りません（必要：{total_required}個、装着：{total_attached}個）"
        
        # 各タイプ別の詳細チェック
        specific_requirements = {}
        colorless_requirement = 0
        
        for energy_type, count in cost_types.items():
            # 無色エネルギーは後で処理
            if energy_type in ['無色', 'colorless', 'Colorless', 'ノーマル']:
                colorless_requirement += count
            else:
                specific_requirements[energy_type] = count
        
        # 特定タイプのエネルギー要求をチェック
        used_for_specific = 0
        missing_specific = []
        
        for required_type, required_count in specific_requirements.items():
            available_count = attached_energy.get(required_type, 0)
            if available_count < required_count:
                missing_count = required_count - available_count
                missing_specific.append(f"{required_type}エネルギー×{missing_count}")
            else:
                used_for_specific += required_count
        
        # 特定タイプが足りない場合
        if missing_specific:
            missing_text = "、".join(missing_specific)
            return False, f"「{attack_name}」は{missing_text}が足りません"
        
        # 無色エネルギーのチェック（残りのエネルギーで支払う）
        if colorless_requirement > 0:
            available_for_colorless = total_attached - used_for_specific
            if available_for_colorless < colorless_requirement:
                missing_colorless = colorless_requirement - available_for_colorless
                return False, f"「{attack_name}」は無色エネルギー×{missing_colorless}が足りません"
        
        # 使用可能
        power_text = f" ({attack_power}ダメージ)" if attack_power else ""
        cost_text = EnergyCostChecker._get_cost_display_text(cost_types, attached_energy)
        return True, f"「{attack_name}」{power_text} - {cost_text}"
    
    @staticmethod
    def _get_cost_display_text(cost_types: Dict[str, int], attached_energy: Dict[str, int]) -> str:
        """エネルギーコストの支払い詳細を表示"""
        details = []
        
        # 特定タイプのエネルギー使用
        used_for_specific = 0
        for energy_type, requirement in cost_types.items():
            if energy_type not in ['無色', 'colorless', 'Colorless', 'ノーマル']:
                details.append(f"{energy_type}: {requirement}/{attached_energy.get(energy_type, 0)}個使用")
                used_for_specific += requirement
        
        # 無色エネルギー使用
        colorless_requirement = sum(count for energy_type, count in cost_types.items() 
                                  if energy_type in ['無色', 'colorless', 'Colorless', 'ノーマル'])
        
        if colorless_requirement > 0:
            total_attached = attached_energy.get("total", 0)
            available_for_colorless = total_attached - used_for_specific
            details.append(f"無色: {colorless_requirement}/{available_for_colorless}個使用")
        
        return "支払い: " + "、".join(details) if details else ""
    
    @staticmethod
    def get_available_attacks(pokemon: Card, game_state=None) -> List[Tuple[int, str, bool, str]]:
        """
        ポケモンの使用可能なワザ一覧を取得（先攻1ターン目攻撃制限対応・無色エネルギー対応版）
        
        Args:
            pokemon: 対象のポケモン
            game_state: ゲーム状態（先攻1ターン目チェック用）
        
        Returns:
            List[Tuple[int, str, bool, str]]: (ワザ番号, ワザ名, 使用可能か, 詳細)
        """
        attacks = []
        
        # ワザ1のチェック
        if pokemon.attack_name:
            can_use, details = EnergyCostChecker.can_use_attack(pokemon, 1, game_state)
            attacks.append((1, pokemon.attack_name, can_use, details))
        
        # ワザ2のチェック
        if hasattr(pokemon, 'attack2_name') and pokemon.attack2_name:
            can_use, details = EnergyCostChecker.can_use_attack(pokemon, 2, game_state)
            attacks.append((2, pokemon.attack2_name, can_use, details))
        
        return attacks
    
    @staticmethod
    def get_energy_status_summary(pokemon: Card) -> str:
        """ポケモンのエネルギー装着状況の要約を取得（無色エネルギー対応版）"""
        attached_energy = EnergyCostChecker._get_attached_energy_summary(pokemon)
        total_energy = attached_energy.get("total", 0)
        
        if total_energy == 0:
            return f"{pokemon.name}: エネルギー未装着"
        
        energy_parts = []
        for energy_type, count in attached_energy.items():
            if energy_type != "total":  # totalは除外
                energy_parts.append(f"{energy_type}×{count}")
        
        energy_text = "、".join(energy_parts)
        return f"{pokemon.name}: {energy_text} (計{total_energy}個)"
    
    @staticmethod
    def get_energy_requirements_analysis(pokemon: Card) -> Dict[str, any]:
        """
        ポケモンのエネルギー要求分析を取得（新機能）
        
        Returns:
            Dict containing detailed energy analysis
        """
        analysis = {
            "attached_summary": EnergyCostChecker._get_attached_energy_summary(pokemon),
            "attacks_analysis": [],
            "optimal_energy_count": 0,
            "missing_for_all_attacks": []
        }
        
        # 各ワザの分析
        if pokemon.attack_name:
            attack1_analysis = EnergyCostChecker._analyze_single_attack(pokemon, 1)
            analysis["attacks_analysis"].append(attack1_analysis)
        
        if hasattr(pokemon, 'attack2_name') and pokemon.attack2_name:
            attack2_analysis = EnergyCostChecker._analyze_single_attack(pokemon, 2)
            analysis["attacks_analysis"].append(attack2_analysis)
        
        # 最適エネルギー数の計算
        if analysis["attacks_analysis"]:
            max_cost = max(attack["total_cost"] for attack in analysis["attacks_analysis"])
            analysis["optimal_energy_count"] = max_cost
        
        return analysis
    
    @staticmethod
    def _analyze_single_attack(pokemon: Card, attack_number: int) -> Dict[str, any]:
        """単一ワザの詳細分析"""
        if attack_number == 1:
            attack_name = pokemon.attack_name
            cost_types = pokemon.attack_cost_types or {}
            attack_power = pokemon.attack_power
        else:
            attack_name = getattr(pokemon, 'attack2_name', '')
            cost_types = getattr(pokemon, 'attack2_cost_types', {}) or {}
            attack_power = getattr(pokemon, 'attack2_power', None)
        
        total_cost = sum(cost_types.values())
        
        analysis = {
            "attack_number": attack_number,
            "attack_name": attack_name,
            "cost_breakdown": cost_types.copy(),
            "total_cost": total_cost,
            "attack_power": attack_power,
            "can_use": False,
            "missing_energy": {}
        }
        
        # 使用可能性チェック（game_stateなしで基本チェックのみ）
        can_use, details = EnergyCostChecker.can_use_attack(pokemon, attack_number)
        analysis["can_use"] = can_use
        analysis["details"] = details
        
        return analysis