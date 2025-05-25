class Pokemon:
    def __init__(
        self,
        name,
        hp,
        ability=None,
        attack1_name=None,
        attack1_text=None,
        attack2_name=None,
        attack2_text=None,
        energy_required=1
    ):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.ability = ability  # 特性
        self.attack1_name = attack1_name  # ワザ1の名前
        self.attack1_text = attack1_text  # ワザ1の効果テキスト
        self.attack2_name = attack2_name  # ワザ2の名前
        self.attack2_text = attack2_text  # ワザ2の効果テキスト
        self.energy_required = energy_required  # 表示用（現状使用しない）

    def take_damage(self, damage):
        """ダメージを受けてHPを減らす"""
        self.current_hp = max(0, self.current_hp - damage)

    def is_knocked_out(self):
        """HPが0以下ならきぜつ"""
        return self.current_hp <= 0

    def __str__(self):
        return f"{self.name}（HP: {self.current_hp}/{self.max_hp}）"
