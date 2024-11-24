
from bomberman.classes import BombermanP1, BombermanP2, BombermanBase
from bomberman.controllers.bonusController import BonusController
from bomberman.controllers.healthController import HealthController
from bomberman.controllers.levelController import LevelController
from bomberman.controllers.scoreController import ScoreController
from bomberman.variables import ARENA_W, SCORE_AREA_H, ARENA_H, SCORE_AREA_W, BLACK, WHITE, BG_GRAY, BG_GREEN, \
    FILENAME_SPRITES

try:
    from __main__ import g2d
except:
    import g2d

from enum import Enum


class Status(Enum):
    LOADING = "Loading"
    PLAY = "Play"
    LOSE = "Lose"
    WIN = "Win"


class LoseOrWinScene:
    def __init__(self, scene_manager):
        self._scene_manager = scene_manager

    def tick(self):
        g2d.clear_canvas()
        g2d.set_color(BLACK)
        g2d.draw_rect((0, 0), (ARENA_W, SCORE_AREA_H + ARENA_H))
        g2d.set_color(WHITE)
        g2d.draw_text("YOU LOSE" if self._scene_manager.get_status() == Status.LOSE else "YOU WIN", (ARENA_W // 2, (SCORE_AREA_H + ARENA_H) // 2 - 10), 20)
        g2d.draw_text("FOR RESET PRESS R", (ARENA_W // 2, (SCORE_AREA_H + ARENA_H) // 2 - 10 + 20), 20)


class LoadScene:
    def __init__(self, scene_manager, level_controller):
        self._timer = 100
        self._scene_manager = scene_manager
        self._level_controller = level_controller

    def tick(self):
        g2d.clear_canvas()
        g2d.set_color((0, 0, 0))
        g2d.draw_rect((0, 0), (ARENA_W, SCORE_AREA_H + ARENA_H))
        g2d.set_color((255, 255, 255))
        g2d.draw_text(f"STAGE {self._level_controller.get_current_level_index()}", (ARENA_W // 2, (SCORE_AREA_H + ARENA_H) // 2 - 10), 20)
        self._timer -= 1
        if self._timer == 0:
            self._scene_manager.set_status(Status.PLAY)


class GameScene:
    def __init__(self, score_gui, arena_gui):
        self._score_gui = score_gui
        self._arena_gui = arena_gui

    def tick(self):
        g2d.clear_canvas()
        self._score_gui.tick()
        self._arena_gui.tick()

class Hud:
    def __init__(self, score_controller, health_controller):
        self._score_controller = score_controller
        self._health_controller = health_controller

    def tick(self):
        g2d.set_color(BG_GRAY)
        g2d.draw_rect((0, 0), (SCORE_AREA_W, SCORE_AREA_H))
        g2d.set_color(WHITE)
        score = self._score_controller.get_score()
        g2d.draw_text(("00" if score == 0 else f"{score}"), (SCORE_AREA_W // 2, SCORE_AREA_H // 2), 14)
        g2d.draw_text(f"P1: LEFT {self._health_controller.get_health(1)}", (SCORE_AREA_W - 86, SCORE_AREA_H // 2), 10)
        g2d.draw_text(f"P2: LEFT {self._health_controller.get_health(2)}", (SCORE_AREA_W - 32, SCORE_AREA_H // 2), 10)

class ArenaScene:
    def __init__(self, level_controller):
        self._level_controller = level_controller
        self.load_objects()

    def load_objects(self):
        for obj in self._level_controller.get_objects():
            self._level_controller.get_arena().spawn(obj)

    def tick(self):
        g2d.set_color(BG_GREEN)
        g2d.draw_rect((0, SCORE_AREA_H), self._level_controller.get_arena().size())

        for a in self._level_controller.get_arena().actors():
            if not isinstance(a, BombermanP1) and not isinstance(a, BombermanP2):
                if a.sprite() != None:
                    g2d.draw_image(FILENAME_SPRITES, a.pos(), a.sprite(), a.size())
                else:
                    pass

        for a in self._level_controller.get_arena().actors():
            if isinstance(a, BombermanP1) or isinstance(a, BombermanP2):
                if a.sprite() != None:
                    g2d.draw_image(FILENAME_SPRITES, a.pos(), a.sprite(), a.size())
                else:
                    pass

        self._level_controller.get_arena().tick(g2d.current_keys())



class SceneManager:
    def __init__(self):
        self._bonus_controller = BonusController()
        self._health_controller = HealthController()
        self._score_controller = ScoreController()
        self._level_controller = LevelController(self, self._bonus_controller, self._health_controller, self._score_controller)
        self._status = Status.LOADING
        self._scenes = {
            Status.LOADING: LoadScene(self, self._level_controller),
            Status.PLAY: GameScene(Hud(self._score_controller, self._health_controller), ArenaScene(self._level_controller)),
            Status.LOSE: LoseOrWinScene(self),
            Status.WIN: LoseOrWinScene(self)
        }

    def set_status(self, status: Status):
        self._status = status

    def get_status(self):
        return self._status

    def next_level(self):
        result = self._level_controller.next_level()

        if result == "WIN":
            self._status = Status.WIN
        else:
            self._scenes[Status.LOADING] = LoadScene(self, self._level_controller)
            self._status = Status.LOADING

            self._scenes[Status.PLAY] = GameScene(Hud(self._score_controller, self._health_controller), ArenaScene(self._level_controller))

    def reset_level(self):
        if self._health_controller.there_is_health():
            self._level_controller.reset_level()
            self._scenes[Status.LOADING] = LoadScene(self, self._level_controller)
            self._status = Status.LOADING

            self._scenes[Status.PLAY] = GameScene(Hud(self._score_controller, self._health_controller), ArenaScene(self._level_controller))
        else:
            self._scenes[Status.LOSE] = LoseOrWinScene(self)
            self._status = Status.LOSE

    def restart(self):
        self._level_controller.restart()
        self._scenes[Status.LOADING] = LoadScene(self, self._level_controller)
        self._status = Status.LOADING
        self._scenes[Status.PLAY] = GameScene(Hud(self._score_controller, self._health_controller), ArenaScene(self._level_controller))

    def tick(self):
        self._scenes[self._status].tick()

        released = set(g2d.previous_keys()) - set(g2d.current_keys())
        if "Escape" in released:
            g2d.close_canvas()
        elif "r" in released:
            self.restart()


def gui_play():
    g2d.init_canvas((ARENA_W, ARENA_H))
    scene_manager = SceneManager()
    BombermanBase.next_level_callback = scene_manager.next_level
    BombermanBase.reset_level_callback = scene_manager.reset_level

    ui = scene_manager

    g2d.main_loop(ui.tick)
