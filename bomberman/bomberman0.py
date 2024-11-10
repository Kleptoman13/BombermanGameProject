#!/usr/bin/env python3
"""
@author  Michele Tomaiuolo - https://tomamic.github.io/
@license This software is free - https://opensource.org/license/mit
"""

from random import choice, randrange
from actor import Actor, Arena, Point

TILE, STEP = 16, 4

class Ballom(Actor):
    def __init__(self, pos):
        self._x, self._y = pos
        self._x = self._x // TILE * TILE
        self._y = self._y // TILE * TILE
        self._w, self._h = TILE, TILE
        self._speed = STEP
        self._dx, self._dy = choice([(0, -STEP), (STEP, 0), (0, STEP), (-STEP, 0)])

    def move(self, arena: Arena):
        if self._x % TILE == 0 and self._y % TILE == 0:
            self._dx, self._dy = choice([(0, -STEP), (STEP, 0), (0, STEP), (-STEP, 0)])
        self._x += self._dx
        self._y += self._dy

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point:
        return 0, 240


class Wall(Actor):
    def __init__(self, pos):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE

    def move(self, arena: Arena):
        return

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point:
        return 80, 48


class Bomberman(Actor):
    def __init__(self, pos):
        self._x, self._y = pos
        self._dx, self._dy = 0, 0
        self._w, self._h = TILE, TILE
        self._speed = STEP

    def move(self, arena: Arena):
        if self._x % TILE == 0 and self._y % TILE == 0:
            self._dx, self._dy = 0, 0
            keys = arena.current_keys()
            if "ArrowUp" in keys:
                self._dy = -self._speed
            elif "ArrowDown" in keys:
                self._dy = self._speed
            elif "ArrowLeft" in keys:
                self._dx = -self._speed
            elif "ArrowRight" in keys:
                self._dx = self._speed

        self._x += self._dx
        self._y += self._dy

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point:
        return 64, 0


def tick():
    g2d.clear_canvas()
    img = "https://fondinfo.github.io/sprites/bomberman.png"
    for a in arena.actors():
        g2d.draw_image(img, a.pos(), a.sprite(), a.size())

    arena.tick(g2d.current_keys())  # Game logic


def main():
    global g2d, arena
    import g2d  # game classes do not depend on g2d

    arena = Arena((480, 360))
    arena.spawn(Ballom((48, 80)))
    arena.spawn(Ballom((80, 48)))
    arena.spawn(Wall((128, 80)))
    arena.spawn(Bomberman((240, 160)))

    g2d.init_canvas(arena.size())
    g2d.main_loop(tick)

if __name__ == "__main__":
    main()


