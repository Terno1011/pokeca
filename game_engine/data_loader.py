import csv
from game_engine.pokemon import Pokemon

def load_pokemon_data(csv_path):
    pokemons = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            pokemon = Pokemon(
                name=row["name"],
                hp=int(row["hp"]),
                attack_name=row["attack_name"],
                attack_damage=int(row["attack_damage"]),
                energy_required=int(row["energy_required"])
            )
            pokemons.append(pokemon)
    return pokemons
