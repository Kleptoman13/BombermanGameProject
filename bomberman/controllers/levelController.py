import json

from bomberman.actor import Arena
from bomberman.classes import Wall, BombermanP1, BombermanP2, Ballom, BlueBallom, Barrel, Ball, Mud, Ghost, Bear

from bomberman.variables import ARENA_W, ARENA_H, SCORE_AREA_H, TILE


class LevelController:
    def __init__(self, scene_manager, bonus_controller, health_controller, score_controller):
        self._levels = self.load_levels_from_json("levels.json")
        self._bonus_controller = bonus_controller
        self._health_controller = health_controller
        self._score_controller = score_controller
        self._scene_manager = scene_manager
        self._current_level_index = 0
        self._current_level = None
        self._current_bonus_type = None
        self._arena = None
        self.load_level(self._current_level_index)

    @staticmethod
    def load_levels_from_json(filename):
        with open(filename, "r") as file:
            return json.load(file)


    def load_level(self, level_index):
        level_data = self._levels[level_index]
        self._current_level = level_data["map"]
        self._bonus_controller.set_bonus(level_data["bonus_type"])
        self._arena = Arena((ARENA_W, ARENA_H))

    def next_level(self):
        if self._current_level_index < len(self._levels) - 1:
            self._current_level_index += 1
            self.load_level(self._current_level_index)
            self._bonus_controller.reset_taken_bonus()
            self._health_controller.add_health(1)
            self._health_controller.add_health(2)
        else:
            return "WIN"

    def restart(self):
        self._current_level_index = 0
        self.load_level(self._current_level_index)
        self._bonus_controller.reset_all_bonus()
        self._health_controller.reset_health()
        self._score_controller.reset_score()

    def reset_level(self):
        self.load_level(self._current_level_index)

    def get_objects(self):
        objects = []
        x, y = 0, SCORE_AREA_H
        for row in self._current_level:
            for cell in row:
                if cell == 1:
                    objects.append(Wall((x, y), 1, self._bonus_controller))
                elif cell == 2:
                    objects.append(Wall((x, y), 2, self._bonus_controller))
                elif cell == 3 and self._health_controller.get_health(1) > 0:
                    objects.append(BombermanP1((x, y), self._bonus_controller, self._health_controller))
                elif cell == 4 and self._health_controller.get_health(2) > 0:
                    objects.append(BombermanP2((x, y), self._bonus_controller, self._health_controller))
                elif cell == 5:
                    objects.append(Ballom((x, y), self._score_controller))
                elif cell == 6:
                    objects.append(BlueBallom((x, y), self._score_controller))
                elif cell == 7:
                    objects.append(Barrel((x, y), self._score_controller))
                elif cell == 8:
                    objects.append(Ball((x, y), self._score_controller))
                elif cell == 9:
                    objects.append(Mud((x, y), self._score_controller))
                elif cell == 10:
                    objects.append(Ghost((x, y), self._score_controller))
                elif cell == 11:
                    objects.append(Bear((x, y), self._score_controller))
                x += TILE
            x = 0
            y += TILE
        return objects

    def get_bonus_type(self):
        return self._current_bonus_type

    def get_current_level_index(self):
        return self._current_level_index + 1

    def get_levels(self):
        return self._levels

    def get_arena(self):
        return self._arena