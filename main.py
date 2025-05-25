from pokemon import Pokemon
from player import Player
from game import Game

def create_sample_deck():
    return [
        Pokemon("ピカチュウ", 60, "でんげき", 30),
        Pokemon("フシギダネ", 70, "つるのムチ", 20),
        Pokemon("ヒトカゲ", 50, "ひのこ", 30)
    ]

def main():
    print("ポケモンカード 手動対戦シミュレーター")
    deck1 = create_sample_deck()
    deck2 = create_sample_deck()

    player1 = Player("プレイヤー1", deck1)
    player2 = Player("プレイヤー2", deck2)

    player1.select_active_pokemon()
    player2.select_active_pokemon()

    game = Game(player1, player2)

    while True:
        if game.next_turn():
            break

if __name__ == "__main__":
    main()
