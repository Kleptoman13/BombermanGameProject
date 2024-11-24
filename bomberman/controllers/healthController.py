health_p1 = 2
health_p2 = 2

class HealthController:
    def __init__(self):
        self.health = {1: 2, 2: 2}

    def add_health(self, player):
        self.health[player] += 1

    def minus_health(self, player):
        self.health[player] -= 1

    def reset_health(self):
        self.health = {1: 2, 2: 2}

    def there_is_health(self):
        if self.health[1] + self.health[2] <= 0:
            return False
        else:
            return True

    def get_health(self, player):
        return self.health[player]


