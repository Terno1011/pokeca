# database/database_manager.py
# Version: 4.7
# Updated: 2025-06-10 21:00
# CSVベースのデータベース管理クラス：デッキCSV解析エラー修正版

import csv
import os
from typing import List, Dict, Tuple, Optional
from models.card import Card, CardType, TrainerType

class DatabaseManager:
    """CSVファイルを使用したデータベース管理クラス（デッキCSV解析エラー修正版）"""
    
    def __init__(self, cards_csv_path: str = "cards/cards.csv", deck_csv_path: str = "cards/deck.csv"):
        self.cards_csv_path = cards_csv_path
        self.deck_csv_path = deck_csv_path
        self.cards_cache: Dict[int, Card] = {}
        self.decks_cache: Dict[int, List[Tuple[Card, int]]] = {}
        self._load_cards()
        self._load_decks()
    
    def _load_cards(self):
        """カードデータをCSVから読み込み（修正版）"""
        if not os.path.exists(self.cards_csv_path):
            print(f"警告: カードファイル {self.cards_csv_path} が見つかりません")
            return
        
        try:
            with open(self.cards_csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row_num, row in enumerate(reader, start=2):  # ヘッダー行の次から開始
                    try:
                        # コメント行やヘッダー行をスキップ
                        if self._is_comment_or_empty_row(row, 'id'):
                            continue
                            
                        card = self._create_card_from_row(row, row_num)
                        if card:
                            self.cards_cache[card.id] = card
                    except Exception as e:
                        print(f"カードデータ読み込みエラー (行{row_num}, ID: {row.get('id', 'unknown')}): {e}")
            
            print(f"カードデータ読み込み完了: {len(self.cards_cache)}枚")
            
        except Exception as e:
            print(f"カードCSVファイル読み込みエラー: {e}")
    
    def _load_decks(self):
        """デッキデータをCSVから読み込み（修正版）"""
        if not os.path.exists(self.deck_csv_path):
            print(f"警告: デッキファイル {self.deck_csv_path} が見つかりません")
            return
        
        try:
            with open(self.deck_csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                deck_data = {}
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # コメント行やヘッダー行をスキップ（修正：DeckIDフィールドをチェック）
                        if self._is_comment_or_empty_row(row, 'DeckID'):
                            continue
                        
                        deck_id = int(row['DeckID'])
                        card_id = int(row['CardID'])
                        count = int(row['Count'])
                        
                        if card_id in self.cards_cache:
                            if deck_id not in deck_data:
                                deck_data[deck_id] = []
                            deck_data[deck_id].append((self.cards_cache[card_id], count))
                        else:
                            print(f"警告: デッキ{deck_id}で未知のカードID{card_id}が参照されています")
                    
                    except Exception as e:
                        print(f"デッキデータ読み込みエラー (行{row_num}, DeckID: {row.get('DeckID', 'unknown')}): {e}")
                
                self.decks_cache = deck_data
                print(f"デッキデータ読み込み完了: {len(self.decks_cache)}個のデッキ")
                
        except Exception as e:
            print(f"デッキCSVファイル読み込みエラー: {e}")
    
    def _is_comment_or_empty_row(self, row: Dict, id_field: str = 'id') -> bool:
        """コメント行や空行かどうかをチェック（修正版：フィールド名指定可能）"""
        # 指定されたIDフィールドをチェック
        id_value = row.get(id_field, '').strip()
        
        # 空の場合
        if not id_value:
            return True
        
        # コメント行の場合（#で始まる）
        if id_value.startswith('#'):
            return True
        
        # 数値以外の場合（ヘッダー行など）
        try:
            int(id_value)
            return False
        except ValueError:
            return True
    
    def _create_card_from_row(self, row: Dict, row_num: int) -> Optional[Card]:
        """CSV行データからCardオブジェクトを作成（修正版）"""
        try:
            # 基本情報
            card_id = int(row['id'])
            name = row['name'].strip()
            card_type = self._parse_card_type(row['card_type'])
            
            # HP
            hp = None
            if row.get('hp') and str(row['hp']).strip() and str(row['hp']).strip() != 'nan':
                hp_value = str(row['hp']).strip()
                if hp_value.replace('.', '').isdigit():  # 数値かチェック
                    hp = int(float(hp_value))
            
            # ポケモンタイプとエネルギー種類
            pokemon_type = row.get('pokemon_type', '').strip() if row.get('pokemon_type') else None
            energy_kind = row.get('energy_kind', '').strip() if row.get('energy_kind') else None
            
            # 特性
            ability_name = row.get('ability_name', '').strip() if row.get('ability_name') else None
            ability_description = row.get('ability_description', '').strip() if row.get('ability_description') else None
            
            # 攻撃1
            attack_name = row.get('attack_name', '').strip() if row.get('attack_name') else None
            attack_power = self._parse_numeric_field(row.get('attack_power'))
            
            attack_cost_types = self._parse_cost_types(row.get('attack_cost_types', ''))
            attack_cost = self._parse_numeric_field(row.get('attack_cost'))
            
            attack_effect = row.get('attack_effect', '').strip() if row.get('attack_effect') else None
            
            # 攻撃2
            attack2_name = row.get('attack2_name', '').strip() if row.get('attack2_name') else None
            attack2_power = self._parse_numeric_field(row.get('attack2_power'))
            
            attack2_cost_types = self._parse_cost_types(row.get('attack2_cost_types', ''))
            attack2_cost = self._parse_numeric_field(row.get('attack2_cost'))
            
            attack2_effect = row.get('attack2_effect', '').strip() if row.get('attack2_effect') else None
            
            # バトル関連
            weakness = row.get('weakness', '').strip() if row.get('weakness') else None
            resistance = row.get('resistance', '').strip() if row.get('resistance') else None
            retreat_cost = self._parse_numeric_field(row.get('retreat_cost'))
            
            # 進化関連
            evolve_step = self._parse_numeric_field(row.get('evolve_step'), default=0)
            evolves_from = row.get('evolves_from', '').strip() if row.get('evolves_from') else None
            
            # トレーナーカード関連
            trainer_type = None
            trainers_description = None
            if card_type == CardType.TRAINER:
                trainers_type_str = row.get('trainers_type', '').strip()
                if trainers_type_str:
                    trainer_type = self._parse_trainer_type(trainers_type_str)
                
                trainers_description = row.get('trainers_description', '').strip() if row.get('trainers_description') else None
            
            # メタデータ
            rarity = row.get('rarity', '').strip() if row.get('rarity') else None
            regulation = row.get('regulation', '').strip() if row.get('regulation') else None
            
            return Card(
                id=card_id,
                name=name,
                card_type=card_type,
                hp=hp,
                pokemon_type=pokemon_type,
                energy_kind=energy_kind,
                ability_name=ability_name,
                ability_description=ability_description,
                attack_name=attack_name,
                attack_power=attack_power,
                attack_cost_types=attack_cost_types,
                attack_cost=attack_cost,
                attack_effect=attack_effect,
                attack2_name=attack2_name,
                attack2_power=attack2_power,
                attack2_cost_types=attack2_cost_types,
                attack2_cost=attack2_cost,
                attack2_effect=attack2_effect,
                weakness=weakness,
                resistance=resistance,
                retreat_cost=retreat_cost,
                evolve_step=evolve_step,
                evolves_from=evolves_from,
                trainer_type=trainer_type,
                trainers_description=trainers_description,
                rarity=rarity,
                regulation=regulation
            )
        
        except Exception as e:
            print(f"カード作成エラー (行{row_num}): {e}")
            return None
    
    def _parse_numeric_field(self, value, default=None):
        """数値フィールドを解析（修正版）"""
        if not value or str(value).strip() == '' or str(value).strip().lower() == 'nan':
            return default
        
        value_str = str(value).strip()
        
        # 数値でない場合はデフォルト値を返す
        try:
            if '.' in value_str:
                return int(float(value_str))
            else:
                return int(value_str)
        except ValueError:
            return default
    
    def _parse_card_type(self, card_type_str: str) -> CardType:
        """カードタイプ文字列をCardType enumに変換"""
        type_mapping = {
            'ポケモン': CardType.POKEMON,
            'Pokemon': CardType.POKEMON,
            'POKEMON': CardType.POKEMON,
            'エネルギー': CardType.ENERGY,
            'Energy': CardType.ENERGY,
            'ENERGY': CardType.ENERGY,
            'トレーナー': CardType.TRAINER,
            'Trainer': CardType.TRAINER,
            'TRAINER': CardType.TRAINER,
            'ポケモンのどうぐ': CardType.TOOL,
            'Tool': CardType.TOOL,
            'TOOL': CardType.TOOL
        }
        return type_mapping.get(card_type_str, CardType.POKEMON)
    
    def _parse_trainer_type(self, trainer_type_str: str) -> TrainerType:
        """トレーナータイプ文字列をTrainerType enumに変換"""
        type_mapping = {
            'サポート': TrainerType.SUPPORTER,
            'Supporter': TrainerType.SUPPORTER,
            'グッズ': TrainerType.ITEM,
            'Item': TrainerType.ITEM,
            'スタジアム': TrainerType.STADIUM,
            'Stadium': TrainerType.STADIUM,
            'ポケモンのどうぐ': TrainerType.POKEMON_TOOL,
            'Pokemon Tool': TrainerType.POKEMON_TOOL
        }
        return type_mapping.get(trainer_type_str, TrainerType.ITEM)
    
    def _parse_cost_types(self, cost_str: str) -> Optional[Dict[str, int]]:
        """コスト文字列を辞書に変換（修正版）"""
        if not cost_str or cost_str.strip() == '' or cost_str.strip().lower() == 'nan':
            return None
        
        cost_types = {}
        try:
            # セミコロンまたはカンマで分割
            separators = [';', ',']
            parts = [cost_str]
            
            for separator in separators:
                new_parts = []
                for part in parts:
                    new_parts.extend(part.split(separator))
                parts = new_parts
            
            for cost_part in parts:
                cost_part = cost_part.strip()
                if not cost_part:
                    continue
                
                if ':' in cost_part:
                    try:
                        energy_type, count = cost_part.split(':', 1)  # 最初の:のみで分割
                        energy_type = energy_type.strip()
                        count_str = count.strip()
                        
                        if energy_type and count_str:
                            cost_types[energy_type] = int(count_str)
                    except ValueError as ve:
                        print(f"コスト部分解析エラー: {cost_part} - {ve}")
                        continue
                else:
                    # ":"がない場合は無色エネルギー1個として扱う
                    if cost_part.isdigit():
                        cost_types['colorless'] = int(cost_part)
                    elif cost_part:
                        cost_types[cost_part] = 1
        
        except Exception as e:
            print(f"コストタイプ解析エラー: {cost_str} - {e}")
            return None
        
        return cost_types if cost_types else None
    
    def get_card(self, card_id: int) -> Optional[Card]:
        """指定IDのカードを取得"""
        return self.cards_cache.get(card_id)
    
    def get_all_cards(self) -> List[Card]:
        """全カードを取得"""
        return list(self.cards_cache.values())
    
    def get_available_decks(self) -> Dict[int, str]:
        """利用可能なデッキのリストを取得"""
        deck_names = {}
        for deck_id in self.decks_cache.keys():
            # デッキ名を生成（実際のデッキ名データがない場合）
            deck_names[deck_id] = f"デッキ {deck_id}"
        return deck_names
    
    def get_deck_cards(self, deck_id: int) -> List[Tuple[Card, int]]:
        """指定デッキのカードリストを取得"""
        return self.decks_cache.get(deck_id, [])
    
    def search_cards(self, name: str = None, card_type: CardType = None) -> List[Card]:
        """カード検索"""
        results = []
        for card in self.cards_cache.values():
            if name and name.lower() not in card.name.lower():
                continue
            if card_type and card.card_type != card_type:
                continue
            results.append(card)
        return results
    
    def debug_csv_content(self, csv_path: str, max_lines: int = 10):
        """CSV内容をデバッグ表示（トラブルシューティング用）"""
        print(f"\n=== {csv_path} の内容確認 ===")
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for i, line in enumerate(lines[:max_lines], 1):
                    print(f"行{i}: {repr(line.strip())}")
                if len(lines) > max_lines:
                    print(f"... 他 {len(lines) - max_lines} 行")
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
        print("=" * 50)