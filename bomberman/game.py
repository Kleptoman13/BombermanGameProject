import math
import random

import g2d
from actor import Actor, Arena, Point

TILE = 16
taken_bonus = 0
# allowed_bombs_general = 2

class Bonus(Actor):
    def __init__(self, pos, type: int):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE
        self._type = type

    def get_type(self):
        return self._type

    def move(self, arena: "Arena"):
        pass

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point | None:
        if self._type == 1:
            return 0, 224
        elif self._type == 2:
            return 16, 224
        elif self._type == 3:
            return 32, 224
        elif self._type == 4:
            return 48, 224
        elif self._type == 5:
            return 64, 224
        elif self._type == 6:
            return 80, 224
        elif self._type == 7:
            return 96, 224
        elif self._type == 8:
            return 112, 224


class Door(Actor):
    def __init__(self, pos):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE

    def move(self, arena: "Arena"):
        pass

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point | None:
        return 176, 48


class Wall(Actor):
    def __init__(self, pos, type: int):
        self._x, self._y = pos
        self._type = type
        self._w, self._h = TILE, TILE
        self._sprite_type1 = (48, 48)
        self._sprite_type2 = (64, 48)
        self._frames_anim_death = [(160, 48), (144, 48), (128, 48), (112, 48), (96, 48), (80, 48)]
        self._time_death = 20
        self._timer_start = self._time_death
        self._timer_on = False

    def in_explosion(self):
        self._timer_on = True

    def start_anim_death(self):
        global taken_bonus
        if self._type == 2 and self._time_death > 0:
            self._timer_on = True

            frame_duration = self._timer_start // len(self._frames_anim_death)
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death) - 1)

            self._sprite_type2 = self._frames_anim_death[frame_index]
        elif self._time_death == 0 and self._type == 2:
            self._timer_on = False

            total_walls_type2 = len([actor for actor in arena.actors() if isinstance(actor, Wall) and actor._type == 2])
            if total_walls_type2 > 0:
                has_door = any(isinstance(actor, Door) for actor in arena.actors())
                has_bonus = any(isinstance(actor, Bonus) for actor in arena.actors())
                chance = total_walls_type2 // 2 + 1
                value = random.randrange(1, total_walls_type2 + 1)
                if value == chance and not has_door and not has_bonus:
                    if random.choice([True, False]):
                        arena.spawn(Door((self._x, self._y)))
                    else:
                        if taken_bonus == 0:
                            arena.spawn(Bonus((self._x, self._y), 7))
                            taken_bonus += 1
                elif value == chance and has_door and not has_bonus:
                    if taken_bonus == 0:
                        arena.spawn(Bonus((self._x, self._y), 7))
                        taken_bonus += 1
                elif value == chance and has_bonus and not has_door:
                    arena.spawn(Door((self._x, self._y)))

            arena.kill(self)

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1

    def pos(self) -> Point:
        return self._x, self._y

    def get_type(self) -> int:
        return self._type

    def sprite(self) -> Point:
        if self._type == 1:
            return self._sprite_type1
        elif self._type == 2:
            return self._sprite_type2

    def size(self) -> Point:
        return self._w, self._h


class Player(Actor):
    def __init__(self, pos):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE
        self._bombes_allowed = 1
        self._additional_fire_length = 0
        self._speed_boosts = 0
        self._has_detonator = False
        self._speed = 2 + self._speed_boosts * 1
        self._direction = None
        self._frames_anim_walk = [[(0, 0), (16, 0), (32, 0)],  # left
                                  [(48, 0), (64, 0), (80, 0)],  # down
                                  [(0, 16), (16, 16), (32, 16)],  # right
                                  [(48, 16), (64, 16), (80, 16)]]  # up
        self._tick = 0
        self._frame_counter = 0
        self._frame_interval = 3
        self._frames_anim_death = [(96, 32), (80, 32), (64, 32), (48, 32), (32, 32), (16, 32), (0, 32)]
        self._time_death = 60
        self._timer_start = self._time_death
        self._timer_on = False
        self._sprite_death = (0, 32)

    def in_explosion(self):
        self._timer_on = True

    def start_anim_death(self):
        if self._time_death > 0:
            self._timer_on = True

            frame_duration = self._timer_start // len(self._frames_anim_death)
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death) - 1)

            self._sprite_death = self._frames_anim_death[frame_index]
        elif self._time_death == 0:
            self._timer_on = False
            arena.kill(self)

    def hit(self, arena: Arena):
        arena.kill(self)

    def check_collision(self, other, next_pos):
        nx, ny = next_pos
        return nx < other.pos()[0] + other.size()[0] and nx + self._w > other.pos()[0] and ny < other.pos()[1] + other.size()[1] and ny + self._h > other.pos()[1]

    def select(self):
        if self._x % TILE == 0 and self._y % TILE == 0:
            for other in arena.collisions():
                if isinstance(other, Bonus) and other.pos()[0] == self._x and other.pos()[1] == self._y:
                    if other.get_type() == 2:
                        self._additional_fire_length += 1
                    if other.get_type() == 5:
                        self._bombes_allowed += 1
                    if other.get_type() == 7:
                        self._has_detonator = True
                    arena.kill(other)

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point:
        if self._timer_on:
            return self._sprite_death

        if self._direction:
            direction_index = {"left": 0, "down": 1, "right": 2, "up": 3}[self._direction]
            return self._frames_anim_walk[direction_index][self._tick]
        return 16, 0


class BombermanP1(Player):
    def __init__(self, pos):
        super().__init__(pos)

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1
        else:
            keys = arena.current_keys()
            # print(keys)
            if self._x % TILE == 0 and self._y % TILE == 0:
                if "w" in keys:
                    self._direction = "up"
                elif "s" in keys:
                    self._direction = "down"
                elif "a" in keys:
                    self._direction = "left"
                elif "d" in keys:
                    self._direction = "right"
                elif not "w" in keys and not "s" in keys and not "a" in keys and not "d" in keys:
                    self._direction = None

            if "z" in keys:
                self.set_bomb()

            if "LeftShift" in keys:
                self.select()

            if "x" in keys and self._has_detonator:
                for a in arena.actors():
                    if isinstance(a, BombP1):
                        a.explosion_instantly()

            next_x, next_y = self._x, self._y

            if self._direction == "up":
                next_y -= self._speed
            elif self._direction == "down":
                next_y += self._speed
            elif self._direction == "left":
                next_x -= self._speed
            elif self._direction == "right":
                next_x += self._speed
            elif not self._direction:
                next_x = self._x
                next_y = self._y

            if not any(isinstance(other, Wall) and self.check_collision(other, (next_x, next_y)) for other in
                       arena.collisions()):
                self._x, self._y = next_x, next_y

            self._frame_counter += 1
            if self._frame_counter >= self._frame_interval:
                self._tick = (self._tick + 1) % len(self._frames_anim_walk[0])
                self._frame_counter = 0

            aw, ah = arena.size()
            self._x = min(max(self._x, 0), aw - self._w)  # clamp
            self._y = min(max(self._y, 0), ah - self._h)  # clamp

    def set_bomb(self):
        if self._x % 16 == 0 and self._y % 16 == 0:
            if len([actor for actor in arena.actors() if isinstance(actor, BombP1)]) < self._bombes_allowed and not any(isinstance(a, BombP1 or BombP2) and a.pos()[0] == self._x and a.pos()[1] == self._y for a in arena.actors()):
                arena.spawn(BombP1((self._x, self._y), self._additional_fire_length))


class BombermanP2(Player):
    def __init__(self, pos):
        super().__init__(pos)

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1
        else:
            keys = arena.current_keys()
            if self._x % TILE == 0 and self._y % TILE == 0:
                if "ArrowUp" in keys:
                    self._direction = "up"
                elif "ArrowDown" in keys:
                    self._direction = "down"
                elif "ArrowLeft" in keys:
                    self._direction = "left"
                elif "ArrowRight" in keys:
                    self._direction = "right"
                elif not "ArrowUp" in keys and not "ArrowDown" in keys and not "ArrowLeft" in keys and not "ArrowRight" in keys:
                    self._direction = None

            if "RightCtrl" in keys:
                self.set_bomb()

            if "RightShift" in keys:
                self.select()

            if "Enter" in keys and self._has_detonator:
                for a in arena.actors():
                    if isinstance(a, BombP2):
                        a.explosion_instantly()

            next_x, next_y = self._x, self._y

            if self._direction == "up":
                next_y -= self._speed
            elif self._direction == "down":
                next_y += self._speed
            elif self._direction == "left":
                next_x -= self._speed
            elif self._direction == "right":
                next_x += self._speed
            elif not self._direction:
                next_x = self._x
                next_y = self._y

            if not any(isinstance(other, Wall) and self.check_collision(other, (next_x, next_y)) for other in
                       arena.collisions()):
                self._x, self._y = next_x, next_y

            self._frame_counter += 1
            if self._frame_counter >= self._frame_interval:
                self._tick = (self._tick + 1) % len(self._frames_anim_walk[0])
                self._frame_counter = 0

            aw, ah = arena.size()
            self._x = min(max(self._x, 0), aw - self._w)  # clamp
            self._y = min(max(self._y, 0), ah - self._h)  # clamp

    def set_bomb(self):
        if self._x % 16 == 0 and self._y % 16 == 0:
            if len([actor for actor in arena.actors() if isinstance(actor, BombP2)]) < self._bombes_allowed and not any(isinstance(a, BombP1 or BombP2) and a.pos()[0] == self._x and a.pos()[1] == self._y for a in arena.actors()):
                arena.spawn(BombP2((self._x, self._y), self._additional_fire_length))


class Enemy(Actor):
    def __init__(self, pos, walk_frames, death_frames, death_sprite, start_death_time, step):
        self._w, self._h = TILE, TILE
        self._x = round(pos[0] / TILE) * TILE
        self._y = round(pos[1] / TILE) * TILE
        self.direction = random.choice(["up", "down", "right", "left"])
        self.step = step
        self._frames_anim_walk = walk_frames
        self._frames_anim_death = death_frames
        self._sprite_death = death_sprite
        self._tick = 0
        self._frame_counter = 0
        self._frame_interval = 5
        self._time_death = start_death_time
        self._timer_start = start_death_time
        self._timer_on = False

    def in_explosion(self):
        self._timer_on = True

    def start_anim_death(self):
        if self._time_death > 0:
            self._timer_on = True

            frame_duration = self._timer_start // len(self._frames_anim_death)
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death) - 1)

            self._sprite_death = self._frames_anim_death[frame_index]
        elif self._time_death == 0:
            self._timer_on = False
            arena.kill(self)

    def check_collision(self, other, pos):
        x, y = pos
        return x < other.pos()[0] + other.size()[0] and x + self._w > other.pos()[0] and y < other.pos()[1] + other.size()[1] and y + self._h > other.pos()[1]

    def move(self, arena: "Arena"):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1
        else:
            self.basic_movement(arena)
            self.frames_calculate()

    def basic_movement(self, arena):
        next_x, next_y = self._x, self._y

        if self.direction == "up":
            next_y -= self.step
        elif self.direction == "down":
            next_y += self.step
        elif self.direction == "right":
            next_x += self.step
        elif self.direction == "left":
            next_x -= self.step

        aw, ah = arena.size()
        if not any((isinstance(other, Wall) or isinstance(other, BombP1) or isinstance(other, BombP2)) and self.check_collision(other, (next_x, next_y)) for other in arena.collisions()):
            if 0 <= next_x <= aw - self._w and 0 <= next_y <= ah - self._h:
                self._x, self._y = next_x, next_y
            else:
                if next_x < 0 or next_x > aw - self._w:
                    self.direction = random.choice(["up", "down"])
                if next_y < 0 or next_y > ah - self._h:
                    self.direction = random.choice(["left", "right"])

        if self._x % 16 == 0 and self._y % 16 == 0:
            self.direction = random.choice(["up", "down", "right", "left"])


    def frames_calculate(self):
        self._frame_counter += 1
        if self._frame_counter >= self._frame_interval:
            self._tick = (self._tick + 1) % len(self._frames_anim_walk[0])
            self._frame_counter = 0

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point | None:
        if self._timer_on:
            return self._sprite_death

        if self.direction:
            direction_index = {"left": 0, "down": 0, "right": 1, "up": 1}[self.direction]
            return self._frames_anim_walk[direction_index][self._tick]
        return None


class Ballom(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos,
            walk_frames = [[(48, 240), (64, 240), (80, 240)],[(0, 240), (16, 240), (32, 240)]],
            death_frames = [(160, 240), (144, 240), (128, 240), (112, 240), (96, 240)],
            death_sprite = (0, 32),
            start_death_time = 60,
            step = 1
        )


class BlueBallom(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos,
            walk_frames=[[(48, 256), (64, 256), (80, 256)], [(0, 256), (16, 256), (32, 256)]],
            death_frames=[(160, 288), (144, 288), (128, 288), (112, 288), (96, 256)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1
        )


class Barrel(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos,
            walk_frames=[[(48, 272), (64, 272), (80, 272)], [(0, 272), (16, 272), (32, 272)]],
            death_frames=[(160, 272), (144, 272), (128, 272), (112, 272), (96, 272)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1
        )


    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1
        else:
            self.barrel_movement(arena)
            self.frames_calculate()

    def barrel_movement(self, arena):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1
        else:
            next_x, next_y = self._x, self._y

            if self.direction == "up":
                next_y -= self.step
            elif self.direction == "down":
                next_y += self.step
            elif self.direction == "right":
                next_x += self.step
            elif self.direction == "left":
                next_x -= self.step

            aw, ah = arena.size()
            if not any((isinstance(other, Wall) or isinstance(other, BombP1) or isinstance(other, BombP2)) and self.check_collision(other, (next_x, next_y)) for other in arena.collisions()):
                if 0 <= next_x <= aw - self._w and 0 <= next_y <= ah - self._h:
                    self._x, self._y = next_x, next_y
                else:
                    if next_x < 0 or next_x > aw - self._w:
                        self.direction = random.choice(["up", "down"])
                    if next_y < 0 or next_y > ah - self._h:
                        self.direction = random.choice(["left", "right"])
            else:
                if self._x % 16 == 0 and self._y % 16 == 0:
                    if self.direction == "up":
                        self.direction = "down"
                    elif self.direction == "down":
                        self.direction = "up"
                    elif self.direction == "left":
                        self.direction = "right"
                    elif self.direction == "right":
                        self.direction = "left"


class Ball(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos,
            walk_frames=[[(48, 288), (64, 288), (80, 288)], [(0, 288), (16, 288), (32, 288)]],
            death_frames=[(160, 240), (144, 240), (128, 240), (112, 240), (96, 288)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1
        )


class Ghost(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos,
            walk_frames=[[(48, 320), (64, 320), (80, 320)], [(0, 320), (16, 320), (32, 320)]],
            death_frames=[(160, 272), (144, 272), (128, 272), (112, 272), (96, 320)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1
        )

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1
        else:
            self.ghost_movement(arena)
            self.frames_calculate()

    def ghost_movement(self, arena):
        next_x, next_y = self._x, self._y

        if self.direction == "up":
            next_y -= self.step
        elif self.direction == "down":
            next_y += self.step
        elif self.direction == "right":
            next_x += self.step
        elif self.direction == "left":
            next_x -= self.step

        aw, ah = arena.size()
        if not any(((isinstance(other, Wall) and other.get_type() == 1) or isinstance(other, BombP1) or isinstance(other, BombP2)) and self.check_collision(other, (next_x, next_y)) for other in arena.collisions()):
            if 0 <= next_x <= aw - self._w and 0 <= next_y <= ah - self._h:
                self._x, self._y = next_x, next_y
            else:
                if next_x < 0 or next_x > aw - self._w:
                    self.direction = random.choice(["up", "down"])
                if next_y < 0 or next_y > ah - self._h:
                    self.direction = random.choice(["left", "right"])

        if self._x % 16 == 0 and self._y % 16 == 0:
            self.direction = random.choice(["up", "down", "right", "left"])


class Mud(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos,
            walk_frames=[[(48, 304), (64, 304), (80, 304)], [(0, 304), (16, 304), (32, 304)]],
            death_frames=[(160, 288), (144, 288), (128, 288), (112, 288), (96, 304)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=0.5
        )

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death()
            self._time_death -= 1
        else:
            self.mud_movement(arena)
            self.frames_calculate()

    def mud_movement(self, arena):
        next_x, next_y = self._x, self._y

        if self.direction == "up":
            next_y -= self.step
        elif self.direction == "down":
            next_y += self.step
        elif self.direction == "right":
            next_x += self.step
        elif self.direction == "left":
            next_x -= self.step

        aw, ah = arena.size()
        if not any(((isinstance(other, Wall) and other.get_type() == 1) or isinstance(other, BombP1) or isinstance(other, BombP2)) and self.check_collision(other, (next_x, next_y)) for other in arena.collisions()):
            if 0 <= next_x <= aw - self._w and 0 <= next_y <= ah - self._h:
                self._x, self._y = next_x, next_y
            else:
                if next_x < 0 or next_x > aw - self._w:
                    self.direction = random.choice(["up", "down"])
                if next_y < 0 or next_y > ah - self._h:
                    self.direction = random.choice(["left", "right"])

        if self._x % 16 == 0 and self._y % 16 == 0:
            self.direction = random.choice(["up", "down", "right", "left"])


class Bear(Enemy):
    def __init__(self, pos):
        super().__init__(
            pos,
            walk_frames=[[(48, 336), (64, 336), (80, 336)], [(0, 336), (16, 336), (32, 336)]],
            death_frames=[(160, 240), (144, 240), (128, 240), (112, 240), (96, 336)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1
        )


class BombBase(Actor):
    def __init__(self, pos, additional_range):
        self._w, self._h = 16, 16
        self._x, self._y = pos
        self._timer = 100
        self._additional_range = additional_range

    def explosion_instantly(self):
        arena.kill(self)
        arena.spawn(Explosion((self._x, self._y), self._additional_range))

    def move(self, arena: Arena):
        self._timer -= 1
        if self._timer <= 0:
            arena.kill(self)
            arena.spawn(Explosion((self._x, self._y), self._additional_range))

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point:
        if self._timer > 30:
            return 0, 48
        elif 10 < self._timer <= 30:
            return 16, 48
        elif self._timer <= 10:
            return 32, 48

class BombP1(BombBase):
    def __init__(self, pos, additional_range):
        super().__init__(pos, additional_range)


class BombP2(BombBase):
    def __init__(self, pos, additional_range):
        super().__init__(pos, additional_range)


class ExplosionEnd(Actor):
    def __init__(self, pos, direction, time_death):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE
        self._direction = direction
        self._ends_of_explosion = {"left": (0, 96), "up": (32, 64), "right": (64, 96), "down": (32, 128)}  # left_end, up_end, right_end, down_end
        self._frames_anim_death = {
            "left": [(0, 96), (80, 96), (0, 176), (80, 176), (80, 176), (0, 176), (80, 96), (0, 96)],
            "up": [(32, 64), (112, 64), (32, 144), (112, 144), (112, 144), (32, 144), (112, 64), (32, 64)],
            "right": [(64, 96), (144, 96), (64, 176), (144, 176), (144, 176), (64, 176), (144, 96), (64, 96)],
            "down": [(32, 128), (112, 128), (32, 208), (112, 208), (112, 208), (32, 208), (112, 128), (32, 128)]}
        self._sprite_death = None
        self._time_death = time_death
        self._timer_start = self._time_death

    def start_anim_death(self):
        if self._time_death > 0:
            frame_duration = max(1, self._timer_start // len(self._frames_anim_death[self._direction]))
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death[self._direction]) - 1)
            self._sprite_death = self._frames_anim_death[self._direction][frame_index]
        elif self._time_death == 0:
            arena.kill(self)

    def move(self, arena: "Arena"):
        self.start_anim_death()
        self._time_death -= 1

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point | None:
        if self._sprite_death:
            return self._sprite_death
        else:
            pass


class ExplosionBody(Actor):
    def __init__(self, pos, direction, time_death):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE
        self._direction = direction
        self._frames_for_body = {"left": (16, 96), "up": (32, 80), "right": (48, 96), "down": (32, 112)}
        self._frames_anim_death = {"left": [(16, 96), (96, 96) , (16, 176), (96, 176), (96, 176), (16, 176), (96, 96), (16, 96)],
                                   "up": [(32, 80), (112, 80) , (32, 160), (112, 160), (112, 160), (32, 160), (112, 80), (32, 80)],
                                   "right": [(48, 96), (128, 96) , (48, 176), (128, 176), (128, 176), (48, 176), (128, 96), (48, 96)],
                                   "down": [(32, 112), (112, 112) , (32, 192), (112, 192), (112, 192), (32, 192), (112, 112), (32, 112)]}
        self._sprite_death = None
        self._time_death = time_death
        self._timer_start = self._time_death

    def start_anim_death(self):
        if self._time_death > 0:
            frame_duration = max(1, self._timer_start // len(self._frames_anim_death[self._direction]))
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death[self._direction]) - 1)
            self._sprite_death = self._frames_anim_death[self._direction][frame_index]
        elif self._time_death == 0:
            arena.kill(self)

    def move(self, arena: "Arena"):
        self.start_anim_death()
        self._time_death -= 1

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point | None:
        if self._sprite_death:
            return self._sprite_death
        else:
            pass



class Explosion(Actor):
    def __init__(self, pos, additional_range):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE
        self._range = 16 + 16 * additional_range
        self._blocked_directions = {"up": False, "down": False, "left": False, "right": False}
        self._blocked_directions_in_range = {"up": self._range, "down": self._range, "left": self._range, "right": self._range}
        self._logical_x, self._logical_w, self._logical_y, self._logical_h = self._x, self._x + self._w, self._y, self._y + self._h
        self._center_sprite = (32, 96)
        self._frames_anim_death = [(32, 96), (112, 96) , (32, 176), (112, 176), (112, 176), (32, 176), (112, 96), (32, 96)]
        self._time_death = 20
        self._timer_start = self._time_death

    def start_anim_death(self):
        if self._time_death > 0:
            frame_duration = max(1, self._timer_start // len(self._frames_anim_death))
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death) - 1)
            self._center_sprite = self._frames_anim_death[frame_index]
        elif self._time_death == 0:
            arena.kill(self)

    def move(self, arena: Arena):
        self.explode()
        self.start_anim_death()
        if self._time_death == self._timer_start:
            self.render_of_explosion()
        self._time_death -= 1

    def explode(self):

        for actor in arena.actors():
            ax, ay = actor.pos()
            aw, ah = actor.size()

            if self.is_in_explosion_range(ax, ay, aw, ah):
                if isinstance(actor, Wall) and actor.get_type() == 2:
                    actor.in_explosion()
                elif isinstance(actor, (BombermanP1, BombermanP2, Ballom, BlueBallom, Barrel, Ball, Mud, Ghost, Bear)):
                    actor.in_explosion()

    def is_in_explosion_range(self, ax, ay, aw, ah):

        up_explosion = ((self._x < ax + aw < 16 + self._x or self._x <= ax < self._x + 16) and self._logical_y < ay + ah <= self._y + 16)
        down_explosion = ((self._x < ax + aw < 16 + self._x or self._x <= ax < self._x + 16) and self._y + 16 <= ay < self._logical_h)
        right_explosion = ((self._y < ay + ah < 16 + self._y or self._y <= ay < self._y + 16) and self._x + 16 <= ax < self._logical_w)
        left_explosion = ((self._y < ay + ah < 16 + self._y or self._y <= ay < self._y + 16) and self._logical_x < ax + aw <= self._x + 16)

        return up_explosion or down_explosion or right_explosion or left_explosion

    def render_of_explosion(self):
        x, y = self._x - self._range, self._y - self._range

        for actor in arena.actors():
            ax, ay = actor.pos()
            aw, ah = actor.size()

            if ax == self._x and y <= ay <= y + self._range and isinstance(actor, Wall):
                self._blocked_directions["up"] = True
                self._blocked_directions_in_range["up"] = min(self._y - (ay + ah), self._blocked_directions_in_range["up"])
            elif ax == self._x and self._y + 16 <= ay < self._y + 16 + self._range and isinstance(actor, Wall):
                self._blocked_directions["down"] = True
                self._blocked_directions_in_range["down"] = min(ay - (self._y + 16), self._blocked_directions_in_range["down"])
            elif ay == self._y and self._x + 16 <= ax < self._x + 16 + self._range and isinstance(actor, Wall):
                self._blocked_directions["right"] = True
                self._blocked_directions_in_range["right"] = min(ax - (self._x + 16), self._blocked_directions_in_range["right"])
            elif ay == self._y and x <= ax <= x + self._range and isinstance(actor, Wall):
                self._blocked_directions["left"] = True
                self._blocked_directions_in_range["left"] = min(self._x - (ax + aw), self._blocked_directions_in_range["left"])

        print(self._blocked_directions)
        print(self._blocked_directions_in_range)

        self.create_of_explosion_range("up")
        self.create_of_explosion_range("down")
        self.create_of_explosion_range("right")
        self.create_of_explosion_range("left")


    def create_of_explosion_range(self, direction):
        if direction == "up":
            count = self._blocked_directions_in_range[direction] / 16
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x, self._y - 16 * tmp_count), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x, self._y - 16 * count), direction, self._time_death))
            self._logical_y = self._y - self._blocked_directions_in_range["up"] - (16 if self._blocked_directions_in_range["up"] < self._range else 0)
        elif direction == "down":
            count = self._blocked_directions_in_range[direction] / 16
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x, self._y + 16 * tmp_count), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x, self._y + 16 * count), direction, self._time_death))
            self._logical_h = self._y + 16 + self._blocked_directions_in_range["down"] + (16 if self._blocked_directions_in_range["down"] < self._range else 0)
        elif direction == "right":
            count = self._blocked_directions_in_range[direction] / 16
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x + 16 * tmp_count, self._y), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x + 16 * count, self._y), direction, self._time_death))
            self._logical_x = self._x - self._blocked_directions_in_range["left"] - (16 if self._blocked_directions_in_range["left"] < self._range else 0)
        elif direction == "left":
            count = self._blocked_directions_in_range[direction] / 16
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x - 16 * tmp_count, self._y), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x - 16 * count, self._y), direction, self._time_death))
            self._logical_w = self._x + 16 + self._blocked_directions_in_range["right"] + (16 if self._blocked_directions_in_range["right"] < self._range else 0)

    def pos(self):
        return self._x, self._y

    def size(self):
        return self._w, self._h

    def sprite(self):
        return self._center_sprite


def tick():
    g2d.clear_canvas()
    g2d.set_color((60, 123, 1))
    g2d.draw_rect((0, 0), arena.size())

    for a in arena.actors():
        if a.sprite() != None:
            g2d.draw_image("bomberman.png", a.pos(), a.sprite(), a.size())
        else: pass

    arena.tick(g2d.current_keys())


def main():
    global arena

    map = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
           [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 0, 1, 2, 1, 2, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
           [1, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 0, 1, 2, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
           [1, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 2, 1, 2, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
           [1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 2, 1, 0, 1, 2, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
           [1, 0, 2, 0, 0, 2, 2, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1],
           [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

    ARENA_W, ARENA_H = len(map[0]) * TILE, len(map) * TILE

    arena = Arena((ARENA_W, ARENA_H))

    g2d.init_canvas(arena.size())

    x = 0
    y = 0

    for i in range(len(map)):
        for j in range(len(map[i])):
            if map[i][j] == 1:
                arena.spawn(Wall((x, y), 1))
            elif map[i][j] == 2:
                arena.spawn(Wall((x, y), 2))
            x += TILE
        x = 0
        y += TILE

    arena.spawn(BombermanP1((48, 48)))
    arena.spawn(BombermanP2((64, 48)))
    arena.spawn(Ballom((16, 16)))
    arena.spawn(Ballom((272, 144)))
    arena.spawn(BlueBallom((272, 16)))
    arena.spawn(Barrel((240, 16)))
    arena.spawn(Ball((16, 144)))
    arena.spawn(Mud((16, 144)))
    arena.spawn(Ghost((64, 144)))
    arena.spawn(Bear((112, 144)))

    g2d.main_loop(tick, 30)

if __name__ == "__main__":
    main()