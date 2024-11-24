import random

from bomberman.actor import Actor, Arena, Point
from bomberman.variables import TILE


class BombermanBase(Actor):
    next_level_callback = None
    reset_level_callback = None

    def __init__(self, pos, health_controller, bonus_controller, health, bombes_allowed, additional_fire_length, speed, has_detonator):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE,
        self._health_controller = health_controller
        self._bonus_controller = bonus_controller
        self._health = health
        self._bombes_allowed = bombes_allowed
        self._additional_fire_length = additional_fire_length
        self._has_detonator = has_detonator
        self._speed = speed
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

    def start_anim_death(self, arena: Arena, player):
        if self._time_death > 0:
            self._timer_on = True

            frame_duration = self._timer_start // len(self._frames_anim_death)
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death) - 1)

            self._sprite_death = self._frames_anim_death[frame_index]
        elif self._time_death == 0:
            self._timer_on = False
            self._health -= 1
            self._health_controller.minus_health(player)
            if BombermanBase.reset_level_callback:
                BombermanBase.reset_level_callback()
            arena.kill(self)

    def hit(self):
        self._timer_on = True

    def check_collision(self, other, next_pos):
        nx, ny = next_pos
        return nx < other.pos()[0] + other.size()[0] and nx + self._w > other.pos()[0] and ny < other.pos()[1] + other.size()[1] and ny + self._h > other.pos()[1]

    def select(self, arena: Arena, player):
        if self._x % TILE == 0 and self._y % TILE == 0:
            for other in arena.collisions():
                if isinstance(other, Bonus) and other.pos()[0] == self._x and other.pos()[1] == self._y:
                    if other.get_type() == 2:
                        self._additional_fire_length += 1
                        self._bonus_controller.add_additional_fire_length(player)
                    if other.get_type() == 1:
                        self._bombes_allowed += 1
                        self._bonus_controller.add_bombes_allowed(player)
                    if other.get_type() == 3:
                        self._speed += 2
                        self._bonus_controller.add_speed(player)
                    if other.get_type() == 5:
                        self._has_detonator = True
                        self._bonus_controller.add_detonator(player)
                    arena.kill(other)
                elif isinstance(other, Door) and other.pos()[0] == self._x and other.pos()[1] == self._y:
                    if all(not isinstance(actor, Enemy) for actor in arena.actors()):
                        if BombermanBase.next_level_callback:
                            BombermanBase.next_level_callback()


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


class BombermanP1(BombermanBase):
    def __init__(self, pos, bonus_controller, health_controller):
        self._health_controller = health_controller
        self._bonus_controller = bonus_controller
        super().__init__(
            pos,
            self._health_controller,
            self._bonus_controller,
            self._health_controller.get_health(1),
            self._bonus_controller.get_bombes_allowed(1),
            self._bonus_controller.get_additional_fire_length(1),
            self._bonus_controller.get_speed(1),
            self._bonus_controller.get_has_detonator(1)
        )

    def move(self, arena: "Arena"):
        if self._timer_on:
            self.start_anim_death(arena, 1)
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
                self.set_bomb(arena)

            if "LeftShift" in keys:
                self.select(arena, 1)

            if "x" in keys and self._has_detonator:
                for a in arena.actors():
                    if isinstance(a, BombP1):
                        a.explosion_instantly(arena)

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

    def set_bomb(self, arena: Arena):
        if self._x % TILE == 0 and self._y % TILE == 0:
            if len([actor for actor in arena.actors() if isinstance(actor, BombP1)]) < self._bombes_allowed and not any(isinstance(a, BombBase) and a.pos()[0] == self._x and a.pos()[1] == self._y for a in arena.actors()):
                arena.spawn(BombP1((self._x, self._y), self._additional_fire_length))


class BombermanP2(BombermanBase):
    def __init__(self, pos, bonus_controller, health_controller):
        self._health_controller = health_controller
        self._bonus_controller = bonus_controller
        super().__init__(
            pos,
            self._health_controller,
            self._bonus_controller,
            self._health_controller.get_health(2),
            self._bonus_controller.get_bombes_allowed(2),
            self._bonus_controller.get_additional_fire_length(2),
            self._bonus_controller.get_speed(2),
            self._bonus_controller.get_has_detonator(2)
        )

    def move(self, arena: "Arena"):
        if self._timer_on:
            self.start_anim_death(arena, 2)
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
                self.set_bomb(arena)

            if "RightShift" in keys:
                self.select(arena, 2)

            if "Enter" in keys and self._has_detonator:
                for a in arena.actors():
                    if isinstance(a, BombP2):
                        a.explosion_instantly(arena)

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

    def set_bomb(self, arena: Arena):
        if self._x % 16 == 0 and self._y % 16 == 0:
            if len([actor for actor in arena.actors() if isinstance(actor, BombP2)]) < self._bombes_allowed and not any(isinstance(a, BombBase) and a.pos()[0] == self._x and a.pos()[1] == self._y for a in arena.actors()):
                arena.spawn(BombP2((self._x, self._y), self._additional_fire_length))


class Enemy(Actor):
    def __init__(self, pos, walk_frames, death_frames, death_sprite, start_death_time, step, points, score_controller):
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
        self._score_controller = score_controller
        self._points = points
        self._timer_on = False

    def in_explosion(self):
        self._timer_on = True

    def start_anim_death(self, arena: Arena):
        if self._time_death > 0:
            self._timer_on = True

            frame_duration = self._timer_start // len(self._frames_anim_death)
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death) - 1)

            self._sprite_death = self._frames_anim_death[frame_index]
        elif self._time_death == 0:
            self._timer_on = False
            arena.spawn(Score((self._x, self._y), self._points, self._score_controller))
            arena.kill(self)

    def check_collision(self, other, pos):
        x, y = pos
        return x < other.pos()[0] + other.size()[0] and x + self._w > other.pos()[0] and y < other.pos()[1] + other.size()[1] and y + self._h > other.pos()[1]

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death(arena)
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


        if self._x % TILE == 0 and self._y % TILE == 0:
            self.direction = random.choice(["up", "down", "right", "left"])

        for other in arena.collisions():
            if isinstance(other, BombermanP1) or isinstance(other, BombermanP2):
                if self._x < other.pos()[0] + other.size()[0] and self._x + self._w > other.pos()[0] and self._y < other.pos()[1] + other.size()[1] and self._y + self._h > other.pos()[1]:
                    other.hit()


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
    def __init__(self, pos, score_controller):
        super().__init__(
            pos,
            walk_frames = [[(48, 240), (64, 240), (80, 240)],[(0, 240), (16, 240), (32, 240)]],
            death_frames = [(160, 240), (144, 240), (128, 240), (112, 240), (96, 240)],
            death_sprite = (0, 32),
            start_death_time = 60,
            step = 1,
            points = 100,
            score_controller = score_controller
        )


class BlueBallom(Enemy):
    def __init__(self, pos, score_controller):
        super().__init__(
            pos,
            walk_frames=[[(48, 256), (64, 256), (80, 256)], [(0, 256), (16, 256), (32, 256)]],
            death_frames=[(160, 288), (144, 288), (128, 288), (112, 288), (96, 256)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=2,
            points=200,
            score_controller = score_controller
        )


class Barrel(Enemy):
    def __init__(self, pos, score_controller):
        super().__init__(
            pos,
            walk_frames=[[(48, 272), (64, 272), (80, 272)], [(0, 272), (16, 272), (32, 272)]],
            death_frames=[(160, 272), (144, 272), (128, 272), (112, 272), (96, 272)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1,
            points=400,
            score_controller = score_controller
        )


    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death(arena)
            self._time_death -= 1
        else:
            self.barrel_movement(arena)
            self.frames_calculate()

    def barrel_movement(self, arena):
        if self._timer_on:
            self.start_anim_death(arena)
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
                if self._x % TILE == 0 and self._y % TILE == 0:
                    if self.direction == "up":
                        self.direction = "down"
                    elif self.direction == "down":
                        self.direction = "up"
                    elif self.direction == "left":
                        self.direction = "right"
                    elif self.direction == "right":
                        self.direction = "left"


class Ball(Enemy):
    def __init__(self, pos, score_controller):
        super().__init__(
            pos,
            walk_frames=[[(48, 288), (64, 288), (80, 288)], [(0, 288), (16, 288), (32, 288)]],
            death_frames=[(160, 240), (144, 240), (128, 240), (112, 240), (96, 288)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=2,
            points=800,
            score_controller = score_controller
        )

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death(arena)
            self._time_death -= 1
        else:
            self.ball_movement(arena)
            self.frames_calculate()

    def ball_movement(self, arena):
        if self._timer_on:
            self.start_anim_death(arena)
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
                if self._x % TILE == 0 and self._y % TILE == 0:
                    if self.direction == "up":
                        self.direction = "down"
                    elif self.direction == "down":
                        self.direction = "up"
                    elif self.direction == "left":
                        self.direction = "right"
                    elif self.direction == "right":
                        self.direction = "left"


class Mud(Enemy):
    def __init__(self, pos, score_controller):
        super().__init__(
            pos,
            walk_frames=[[(48, 304), (64, 304), (80, 304)], [(0, 304), (16, 304), (32, 304)]],
            death_frames=[(160, 288), (144, 288), (128, 288), (112, 288), (96, 304)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=0.5,
            points=100,
            score_controller = score_controller
        )

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death(arena)
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

        if self._x % TILE == 0 and self._y % TILE == 0:
            self.direction = random.choice(["up", "down", "right", "left"])


class Ghost(Enemy):
    def __init__(self, pos, score_controller):
        super().__init__(
            pos,
            walk_frames=[[(48, 320), (64, 320), (80, 320)], [(0, 320), (16, 320), (32, 320)]],
            death_frames=[(160, 272), (144, 272), (128, 272), (112, 272), (96, 320)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1,
            points=100,
            score_controller = score_controller
        )

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death(arena)
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

        if self._x % TILE == 0 and self._y % TILE == 0:
            self.direction = random.choice(["up", "down", "right", "left"])


class Bear(Enemy):
    def __init__(self, pos, score_controller):
        super().__init__(
            pos,
            walk_frames=[[(48, 336), (64, 336), (80, 336)], [(0, 336), (16, 336), (32, 336)]],
            death_frames=[(160, 240), (144, 240), (128, 240), (112, 240), (96, 336)],
            death_sprite=(0, 32),
            start_death_time=60,
            step=1,
            points=100,
            score_controller = score_controller
        )


class Wall(Actor):
    def __init__(self, pos, type: int, bonus_controller):
        self._x, self._y = pos
        self._type = type
        self._w, self._h = TILE, TILE
        self._bonus_controller = bonus_controller
        self._sprite_type1 = (48, 48)
        self._sprite_type2 = (64, 48)
        self._frames_anim_death = [(160, 48), (144, 48), (128, 48), (112, 48), (96, 48), (80, 48)]
        self._time_death = 20
        self._timer_start = self._time_death
        self._timer_on = False

    def in_explosion(self):
        self._timer_on = True

    def start_anim_death(self, arena: Arena):
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
                        if self._bonus_controller.get_taken_bonus() == 0:
                            arena.spawn(Bonus((self._x, self._y), self._bonus_controller.get_bonus()))
                            self._bonus_controller.add_taken_bonus()
                elif value == chance and has_door and not has_bonus:
                    if self._bonus_controller.get_taken_bonus() == 0:
                        arena.spawn(Bonus((self._x, self._y), self._bonus_controller.get_bonus()))
                        self._bonus_controller.add_taken_bonus()
                elif value == chance and has_bonus and not has_door:
                    arena.spawn(Door((self._x, self._y)))

            arena.kill(self)

    def move(self, arena: Arena):
        if self._timer_on:
            self.start_anim_death(arena)
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


class BombBase(Actor):
    def __init__(self, pos, additional_range):
        self._w, self._h = TILE, TILE
        self._x, self._y = pos
        self._timer = 100
        self._additional_range = additional_range

    def explosion_instantly(self, arena):
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


class Explosion(Actor):
    def __init__(self, pos, additional_range):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE
        self._range = TILE + TILE * additional_range
        self._blocked_directions = {"up": False, "down": False, "left": False, "right": False}
        self._blocked_directions_in_range = {"up": self._range, "down": self._range, "left": self._range, "right": self._range}
        self._logical_x, self._logical_w, self._logical_y, self._logical_h = self._x, self._x + self._w, self._y, self._y + self._h
        self._center_sprite = (32, 96)
        self._frames_anim_death = [(32, 96), (112, 96) , (32, 176), (112, 176), (112, 176), (32, 176), (112, 96), (32, 96)]
        self._time_death = 20
        self._timer_start = self._time_death

    def start_anim_death(self, arena: Arena):
        if self._time_death > 0:
            frame_duration = max(1, self._timer_start // len(self._frames_anim_death))
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death) - 1)
            self._center_sprite = self._frames_anim_death[frame_index]
        elif self._time_death == 0:
            arena.kill(self)

    def move(self, arena: Arena):
        self.explode(arena)
        self.start_anim_death(arena)
        if self._time_death == self._timer_start:
            self.render_of_explosion(arena)
        self._time_death -= 1

    def explode(self, arena: Arena):

        for actor in arena.actors():
            ax, ay = actor.pos()
            aw, ah = actor.size()

            if self.is_in_explosion_range(ax, ay, aw, ah):
                if isinstance(actor, Wall) and actor.get_type() == 2:
                    actor.in_explosion()
                elif isinstance(actor, (BombermanP1, BombermanP2, Enemy)):
                    actor.in_explosion()

    def is_in_explosion_range(self, ax, ay, aw, ah):

        up_explosion = ((self._x < ax + aw < TILE + self._x or self._x <= ax < self._x + TILE) and self._logical_y < ay + ah <= self._y + TILE)
        down_explosion = ((self._x < ax + aw < TILE + self._x or self._x <= ax < self._x + TILE) and self._y + TILE <= ay < self._logical_h)
        right_explosion = ((self._y < ay + ah < TILE + self._y or self._y <= ay < self._y + TILE) and self._x + TILE <= ax < self._logical_w)
        left_explosion = ((self._y < ay + ah < TILE + self._y or self._y <= ay < self._y + TILE) and self._logical_x < ax + aw <= self._x + TILE)

        return up_explosion or down_explosion or right_explosion or left_explosion

    def render_of_explosion(self, arena: Arena):
        x, y = self._x - self._range, self._y - self._range

        for actor in arena.actors():
            ax, ay = actor.pos()
            aw, ah = actor.size()

            if ax == self._x and y <= ay <= y + self._range and isinstance(actor, Wall):
                self._blocked_directions["up"] = True
                self._blocked_directions_in_range["up"] = min(self._y - (ay + ah), self._blocked_directions_in_range["up"])
            elif ax == self._x and self._y + TILE <= ay < self._y + TILE + self._range and isinstance(actor, Wall):
                self._blocked_directions["down"] = True
                self._blocked_directions_in_range["down"] = min(ay - (self._y + TILE), self._blocked_directions_in_range["down"])
            elif ay == self._y and self._x + TILE <= ax < self._x + TILE + self._range and isinstance(actor, Wall):
                self._blocked_directions["right"] = True
                self._blocked_directions_in_range["right"] = min(ax - (self._x + TILE), self._blocked_directions_in_range["right"])
            elif ay == self._y and x <= ax <= x + self._range and isinstance(actor, Wall):
                self._blocked_directions["left"] = True
                self._blocked_directions_in_range["left"] = min(self._x - (ax + aw), self._blocked_directions_in_range["left"])

        self.create_of_explosion_range("up", arena)
        self.create_of_explosion_range("down", arena)
        self.create_of_explosion_range("right", arena)
        self.create_of_explosion_range("left", arena)


    def create_of_explosion_range(self, direction, arena: Arena):
        if direction == "up":
            count = self._blocked_directions_in_range[direction] / TILE
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x, self._y - TILE * tmp_count), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x, self._y - TILE * count), direction, self._time_death))
            self._logical_y = self._y - self._blocked_directions_in_range["up"] - (16 if self._blocked_directions_in_range["up"] < self._range else 0)
        elif direction == "down":
            count = self._blocked_directions_in_range[direction] / TILE
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x, self._y + TILE * tmp_count), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x, self._y + TILE * count), direction, self._time_death))
            self._logical_h = self._y + TILE + self._blocked_directions_in_range["down"] + (TILE if self._blocked_directions_in_range["down"] < self._range else 0)
        elif direction == "right":
            count = self._blocked_directions_in_range[direction] / TILE
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x + TILE * tmp_count, self._y), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x + TILE * count, self._y), direction, self._time_death))
            self._logical_x = self._x - self._blocked_directions_in_range["left"] - (TILE if self._blocked_directions_in_range["left"] < self._range else 0)
        elif direction == "left":
            count = self._blocked_directions_in_range[direction] / TILE
            if count >= 1:
                tmp_count = count
                while tmp_count > 1:
                    tmp_count -= 1
                    arena.spawn(ExplosionBody((self._x - TILE * tmp_count, self._y), direction, self._time_death))
                if tmp_count == 1:
                    arena.spawn(ExplosionEnd((self._x - TILE * count, self._y), direction, self._time_death))
            self._logical_w = self._x + TILE + self._blocked_directions_in_range["right"] + (TILE if self._blocked_directions_in_range["right"] < self._range else 0)

    def pos(self):
        return self._x, self._y

    def size(self):
        return self._w, self._h

    def sprite(self):
        return self._center_sprite


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

    def start_anim_death(self, arena: Arena):
        if self._time_death > 0:
            frame_duration = max(1, self._timer_start // len(self._frames_anim_death[self._direction]))
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death[self._direction]) - 1)
            self._sprite_death = self._frames_anim_death[self._direction][frame_index]
        elif self._time_death == 0:
            arena.kill(self)

    def move(self, arena: Arena):
        self.start_anim_death(arena)
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

    def start_anim_death(self, arena: Arena):
        if self._time_death > 0:
            frame_duration = max(1, self._timer_start // len(self._frames_anim_death[self._direction]))
            frame_index = (self._time_death - 1) // frame_duration
            frame_index = min(frame_index, len(self._frames_anim_death[self._direction]) - 1)
            self._sprite_death = self._frames_anim_death[self._direction][frame_index]
        elif self._time_death == 0:
            arena.kill(self)

    def move(self, arena: "Arena"):
        self.start_anim_death(arena)
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


class Score(Actor):
    def __init__(self, pos, points, score_controller):
        if points > 999:
            self._w = TILE * 2
        else:
            self._w = TILE
        self._h =  TILE // 2
        self._x = round(pos[0] / TILE) * TILE
        self._y = round(pos[1] / TILE) * TILE
        self._points = points
        self._timer = 20
        self._score_controller = score_controller
        self._score_controller.score_handler(points)

    def move(self, arena: Arena):
        self._timer -= 1
        if self._timer <= 0:
            arena.kill(self)

    def size(self) -> Point:
        return self._w, self._h

    def pos(self) -> Point:
        return self._x, self._y

    def sprite(self) -> Point | None:
        if self._points == 100:
            return 112, 336
        if self._points == 200:
            return 112, 344
        if self._points == 400:
            return 112, 352
        if self._points == 800:
            return 112, 360
        if self._points == 1000:
            return 128, 336
        if self._points == 2000:
            return 128, 344
        if self._points == 4000:
            return 128, 352
        if self._points == 8000:
            return 112, 360


class Bonus(Actor):
    def __init__(self, pos, type: int):
        self._x, self._y = pos
        self._w, self._h = TILE, TILE
        self._type = type

    def get_type(self):
        return self._type

    def move(self, arena: Arena):
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

    def move(self, arena: Arena):
        pass

    def pos(self) -> Point:
        return self._x, self._y

    def size(self) -> Point:
        return self._w, self._h

    def sprite(self) -> Point | None:
        return 176, 48