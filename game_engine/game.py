class Game:
    def __init__(self, player1, player2):
        self.players = [player1, player2]
        self.turn = 0

    def next_turn(self):
        self.turn += 1
        attacker = self.players[self.turn % 2]
        defender = self.players[(self.turn + 1) % 2]

        print(f"\n--- ターン {self.turn} ---")
        print(f"{attacker.name} の番")

        print(f"{attacker.name} のバトルポケモン: {attacker.battle_pokemon}")
        print(f"{defender.name} のバトルポケモン: {defender.battle_pokemon}")

        act = input(f"{attacker.name} の行動（'a'で攻撃, 's'でスキップ）: ")
        if act.lower() == 'a':
            damage = attacker.battle_pokemon.attack_damage
            print(f"{attacker.battle_pokemon.name} の {attacker.battle_pokemon.attack_name}！ {damage} ダメージ")
            defender.battle_pokemon.take_damage(damage)

            if defender.battle_pokemon.is_knocked_out():
                print(f"{defender.battle_pokemon.name} は きぜつ した！")
                defender.battle_pokemon = None
                attacker.receive_prize()

                if defender.has_lost():
                    print(f"\n{attacker.name} の勝利！")
                    return True

                defender.battle_pokemon = defender.select_active_pokemon()
                if defender.battle_pokemon:
                    print(f"{defender.name} は {defender.battle_pokemon.name} をバトル場に出した。")

        return False
