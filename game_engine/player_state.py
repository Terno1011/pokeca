class PlayerState:
    def __init__(self, name, deck):
        self.name = name
        self.deck = deck
        self.hand = []
        self.bench = []
        self.active = None
        self.side_cards = []  # リストに変更（元のコードでは数値だったが、実際にはカードのリストが必要）
        self.trash = []  # トラッシュを追加

    def draw(self, n=1):
        """山札からカードを引く"""
        for _ in range(n):
            if self.deck:
                self.hand.append(self.deck.pop(0))

    def play_to_battle(self, pokemon):
        """手札からバトル場にポケモンを出す"""
        if pokemon in self.hand:
            self.active = pokemon
            self.hand.remove(pokemon)

    def play_to_bench(self, pokemon):
        """手札からベンチにポケモンを出す"""
        if len(self.bench) < 5 and pokemon in self.hand:
            self.bench.append(pokemon)
            self.hand.remove(pokemon)

    def check_knockout(self):
        """バトルポケモンのきぜつをチェック"""
        if self.active and self.active.current_hp <= 0:
            self.active = None
            # サイドカードがある場合、相手がサイドを取る
            return True
        return False

    def switch_pokemon(self, bench_index):
        """ベンチのポケモンとバトルポケモンを交代"""
        if 0 <= bench_index < len(self.bench) and self.active:
            # 現在のバトルポケモンをベンチに戻す
            self.bench.append(self.active)
            # ベンチのポケモンをバトル場に出す
            self.active = self.bench.pop(bench_index)

    def has_lost(self):
        """敗北条件をチェック"""
        # バトルポケモンがいない、かつベンチも空の場合
        return self.active is None and len(self.bench) == 0

    def send_to_trash(self, pokemon, from_location):
        """ポケモンをトラッシュに送る"""
        if from_location == "hand" and pokemon in self.hand:
            self.hand.remove(pokemon)
            self.trash.append(pokemon)
            return True
        elif from_location == "bench" and pokemon in self.bench:
            self.bench.remove(pokemon)
            self.trash.append(pokemon)
            return True
        elif from_location == "active" and pokemon == self.active:
            self.active = None
            self.trash.append(pokemon)
            return True
        return False