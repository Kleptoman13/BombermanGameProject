class BonusController:
    def __init__(self):
        self._bonus = 1
        self._taken_bonus = 0
        self.bombes_allowed = {1: 1, 2: 1}
        self.additional_fire_length = {1: 0, 2: 0}
        self.speed = {1: 2, 2: 2}
        self.has_detonator = {1: False, 2: False}

    def set_bonus(self, bonus_type):
        self._bonus = bonus_type

    def get_bonus(self):
        return self._bonus

    def add_taken_bonus(self):
        self._taken_bonus += 1

    def reset_taken_bonus(self):
        self._taken_bonus = 0

    def get_taken_bonus(self):
        return self._taken_bonus

    def add_bombes_allowed(self, player):
        self.bombes_allowed[player] += 1

    def reset_bombes_allowed(self, player):
        self.bombes_allowed[player] = 1

    def get_bombes_allowed(self, player):
        return self.bombes_allowed[player]

    def add_additional_fire_length(self, player):
        self.additional_fire_length[player] += 1

    def reset_additional_fire_length(self, player):
        self.additional_fire_length[player] = 0

    def get_additional_fire_length(self, player):
        return self.additional_fire_length[player]

    def add_speed(self, player):
        self.speed[player] += 2

    def reset_speed(self, player):
        self.speed[player] = 2

    def get_speed(self, player):
        return self.speed[player]

    def add_detonator(self, player):
        self.has_detonator[player] = True

    def reset_has_detonator(self, player):
        self.has_detonator[player] = False

    def get_has_detonator(self, player):
        return self.has_detonator[player]

    def reset_all_bonus(self):
        self._bonus = 1
        self._taken_bonus = 0
        self.bombes_allowed = {1: 1, 2: 1}
        self.additional_fire_length = {1: 0, 2: 0}
        self.speed = {1: 2, 2: 2}
        self.has_detonator = {1: False, 2: False}