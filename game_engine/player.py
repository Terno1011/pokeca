class Player:
    def __init__(self, name, deck):
        self.name = name
        self.deck = deck
        self.battle_pokemon = None
        self.bench = []
        self.side_cards = 6

    def select_active_pokemon(self):
        if not self.deck:
            return None
        self.battle_pokemon = self.deck.pop(0)
        return self.battle_pokemon

    def receive_prize(self):
        if self.side_cards > 0:
            self.side_cards -= 1

    def has_lost(self):
        return self.battle_pokemon is None and not self.bench
