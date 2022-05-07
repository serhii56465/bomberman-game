import random
import pygame

from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE
from abc import ABC, abstractmethod

from mixins import MovingMixin, EngineMixin
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DEFAULT_OBJ_SIZE,
    DEFAULT_PLAYER_HP,
    DEFAULT_PLAYER_SPEED,
    BOMB_TIMER,
    PLANT_BOMB_COOLDOWN,
    BOMB_EXPLODE_RANGE,
    FIRE_LIFETIME
)


class EngineSprite(EngineMixin, pygame.sprite.Sprite):
    pass


class EngineMovingSprite(MovingMixin, EngineSprite):
    pass


class Player(EngineMovingSprite):
    def __init__(self):
        super(Player, self).__init__()
        self.engine.add_to_group(self, "player")
        self.engine.add_to_group(self, "flammable")
        self.surf = pygame.image.load(
            "images/player_front.png"
        ).convert_alpha()
        self.rect = self.surf.get_rect()
        self.plant_bomb_cooldown = 0
        self.is_on_bomb = False
        self.health = DEFAULT_PLAYER_HP
        self.speed = DEFAULT_PLAYER_SPEED

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        if self.health <= 0:
            self.kill()

        if self.plant_bomb_cooldown:
            self.plant_bomb_cooldown -= 1

        if not pygame.sprite.spritecollideany(
                self,
                self.engine.groups["bombs"]
        ):
            self.is_on_bomb = False

        if pressed_keys[K_UP]:
            self.rect.move_ip(0, -self.speed)
            self.move_collision_out(0, -self.speed)
            self.surf = pygame.image.load(
                "images/player_back.png"
            ).convert_alpha()

        if pressed_keys[K_DOWN]:
            self.rect.move_ip(0, self.speed)
            self.move_collision_out(0, self.speed)
            self.surf = pygame.image.load(
                "images/player_front.png"
            ).convert_alpha()

        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-self.speed, 0)
            self.move_collision_out(-self.speed, 0)
            self.surf = pygame.image.load(
                "images/player_left.png"
            ).convert_alpha()

        if pressed_keys[K_RIGHT]:
            self.rect.move_ip(self.speed, 0)
            self.move_collision_out(self.speed, 0)
            self.surf = pygame.image.load(
                "images/player_right.png"
            ).convert_alpha()

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        if pressed_keys[K_SPACE]:
            self.place_bomb()

    def place_bomb(self):
        if not self.plant_bomb_cooldown:
            self.is_on_bomb = True
            Bomb(self.rect.center)
            self.plant_bomb_cooldown = PLANT_BOMB_COOLDOWN

    def change_health(self, hp: int):
        self.health += hp

    def change_speed(self, sp: int):
        self.speed += sp

    def get_health(self):
        return self.health

    def get_speed(self):
        return self.speed

    def kill(self) -> None:
        super().kill()
        self.engine.running = False


class Wall(EngineSprite):
    def __init__(self, center_pos: tuple):
        super().__init__()
        self.engine.add_to_group(self, "walls")
        self.surf = pygame.image.load("images/wall.png").convert_alpha()
        self.rect = self.surf.get_rect(center=center_pos)

    @classmethod
    def generate_walls(cls, field_size: tuple, wall_size: tuple):
        walls_centers = cls.create_centers_of_walls(field_size, wall_size)
        for obs_center in walls_centers:
            Wall(obs_center)

    @staticmethod
    def create_centers_of_walls(field_size: tuple, wall_size: tuple):
        center_width = wall_size[0] + wall_size[0] // 2
        center_height = wall_size[1] + wall_size[1] // 2
        centers = []

        while center_height < field_size[1] - wall_size[1]:
            while center_width < field_size[0] - wall_size[0]:
                centers.append((center_width, center_height))
                center_width += 2 * wall_size[0]
            center_height += 2 * wall_size[1]
            center_width = wall_size[0] + wall_size[0] // 2

        return centers


class Bomb(EngineSprite):
    def __init__(self, owner_center):
        super().__init__()
        self.engine.add_to_group(self, "bombs")
        self.surf = pygame.image.load("images/bomb.png").convert_alpha()
        self.lifetime = BOMB_TIMER
        self.explode_range = BOMB_EXPLODE_RANGE
        self.rect = self.surf.get_rect(
            center=self.get_self_center(owner_center)
        )

    def get_self_center(self, owner_center):
        lines = self.get_line_bomb_placed(owner_center)
        return (
            lines[0] * DEFAULT_OBJ_SIZE + self.surf.get_width() // 2,
            lines[1] * DEFAULT_OBJ_SIZE + self.surf.get_height() // 2,
        )

    @staticmethod
    def get_line_bomb_placed(owner_center):
        width = owner_center[0] // DEFAULT_OBJ_SIZE
        height = owner_center[1] // DEFAULT_OBJ_SIZE
        return width, height

    def update(self):
        self.lifetime -= 1
        if not self.lifetime:
            self.explode()

    def explode(self):
        fires = [(self.rect.centerx, self.rect.centery)]

        width = self.rect.centerx
        for it in range(1, self.explode_range + 1):
            height = self.rect.centery + it * DEFAULT_OBJ_SIZE
            if self.walls_collide_point((width, height)):
                break
            Fire((width, height))

            height = self.rect.centery - it * DEFAULT_OBJ_SIZE
            if self.walls_collide_point((width, height)):
                break
            Fire((width, height))

        height = self.rect.centery
        for it in range(1, self.explode_range + 1):
            width = self.rect.centerx + it * DEFAULT_OBJ_SIZE
            if self.walls_collide_point((width, height)):
                break
            Fire((width, height))

            width = self.rect.centerx - it * DEFAULT_OBJ_SIZE
            if self.walls_collide_point((width, height)):
                break
            Fire((width, height))

        for item in fires:
            Fire(item)
        self.kill()

    def walls_collide_point(self, point):
        for sprite in self.engine.groups["walls"].sprites():
            if sprite.rect.collidepoint(point):
                return True
        return False


class Fire(EngineSprite):
    def __init__(self, center_pos: tuple):
        super().__init__()
        self.engine.add_to_group(self, "fires")
        self.width = DEFAULT_OBJ_SIZE
        self.height = DEFAULT_OBJ_SIZE
        self.surf = pygame.image.load("images/explosion_1.png").convert_alpha()
        self.rect = self.surf.get_rect(center=(center_pos[0], center_pos[1]))
        self.lifetime = FIRE_LIFETIME

    def update(self):
        self.lifetime -= 1

        if self.lifetime < 0:
            self.kill()
        elif self.lifetime < 3:
            self.surf = pygame.image.load(
                "images/explosion_3.png"
            ).convert_alpha()
        elif self.lifetime < 6:
            self.surf = pygame.image.load(
                "images/explosion_2.png"
            ).convert_alpha()

        # kill all flammable units that touch the fire
        flamed = pygame.sprite.spritecollideany(
            self, self.engine.groups["flammable"]
        )
        if flamed:
            flamed.kill()


class Enemy(EngineMovingSprite, ABC):
    def __init__(self):
        super().__init__()
        self.speed = 2
        self.position = self.generate_position()
        self.surf = pygame.Surface((20, 10))
        self.rect = self.surf.get_rect(center=self.position[:2])
        self.score_points = 10

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def collisions_handling(self):
        pass

    @abstractmethod
    def move(self):
        pass

    @staticmethod
    def generate_position() -> tuple:
        delta = 50
        direction = random.choice(["left", "top", "right", "bottom"])
        if direction == "left":
            width = -delta
            height = random.randint(0, SCREEN_HEIGHT)

        if direction == "top":
            width = random.randint(0, SCREEN_WIDTH)
            height = -delta

        if direction == "right":
            width = SCREEN_WIDTH + delta
            height = random.randint(0, SCREEN_HEIGHT)

        if direction == "bottom":
            width = random.randint(0, SCREEN_WIDTH)
            height = SCREEN_HEIGHT + delta

        return width, height, direction

    def kill(self) -> None:
        super().kill()
        self.engine.score += self.score_points


class Spider(Enemy):
    def __init__(self):
        super().__init__()
        self.engine.add_to_group(self, "spiders")
        self.engine.add_to_group(self, "flammable")
        self.image_front = pygame.image.load(
            "images/spider_front.png"
        ).convert_alpha()
        self.image_back = pygame.image.load(
            "images/spider_back.png"
        ).convert_alpha()
        self.image_left = pygame.image.load(
            "images/spider_left.png"
        ).convert_alpha()
        self.image_right = pygame.image.load(
            "images/spider_right.png"
        ).convert_alpha()
        self.surf = self.image_front

    def update(self):
        self.collisions_handling()
        self.move()

    def collisions_handling(self):
        player = self.engine.groups["player"].sprites()[0]
        if pygame.sprite.spritecollideany(self, self.engine.groups["player"]):
            player.change_health(-10)
            self.kill()

    def move(self):
        player = self.engine.groups["player"].sprites()[0]
        x_diff = self.rect.centerx - player.rect.centerx
        y_diff = self.rect.centery - player.rect.centery

        if not y_diff:
            pass
        elif y_diff < 0:
            self.surf = self.image_front
            self.rect.move_ip(0, self.speed)
            self.move_collision_out(0, self.speed)
        else:
            self.surf = self.image_back
            self.rect.move_ip(0, -self.speed)
            self.move_collision_out(0, -self.speed)
        if not x_diff:
            pass
        elif x_diff < 0:
            self.surf = self.image_right
            self.rect.move_ip(self.speed, 0)
            self.move_collision_out(self.speed, 0)
        else:
            self.surf = self.image_left
            self.rect.move_ip(-self.speed, 0)
            self.move_collision_out(-self.speed, 0)


class Boar(Enemy):
    def __init__(self):
        super().__init__()
        self.engine.add_to_group(self, "boars")
        self.engine.add_to_group(self, "flammable")
        self.image_front = pygame.image.load(
            "images/boar_front.png"
        ).convert_alpha()
        self.image_back = pygame.image.load(
            "images/boar_back.png"
        ).convert_alpha()
        self.image_left = pygame.image.load(
            "images/boar_left.png"
        ).convert_alpha()
        self.image_right = pygame.image.load(
            "images/boar_right.png"
        ).convert_alpha()
        self.surf = self.image_front
        self.plant_rock_count = 0
        self.is_on_rock = False

    def update(self):
        self.collisions_handling()
        self.move()
        if self.plant_rock_count < 180:
            self.plant_rock_count += 1
        elif self.plant_rock_count == 180:
            self.plant_rock()

        if not pygame.sprite.spritecollideany(
                self,
                self.engine.groups["rocks"]
        ):
            self.is_on_rock = False

    def plant_rock(self):
        self.is_on_rock = True
        Rock(self.rect.center)
        self.plant_rock_count = 0

    def collisions_handling(self):
        player = self.engine.groups["player"].sprites()[0]
        if pygame.sprite.spritecollideany(self, self.engine.groups["player"]):
            player.change_health(-10)
            self.kill()
            Healing()
            Slow()
            Accelerate()

    def move(self):
        player = self.engine.groups["player"].sprites()[0]
        x_diff = self.rect.centerx - player.rect.centerx
        y_diff = self.rect.centery - player.rect.centery

        if not y_diff:
            pass
        elif y_diff < 0:
            self.surf = self.image_front
            self.rect.move_ip(0, self.speed)
            self.move_collision_out(0, self.speed)
        else:
            self.surf = self.image_back
            self.rect.move_ip(0, -self.speed)
            self.move_collision_out(0, -self.speed)
        if not x_diff:
            pass
        elif x_diff < 0:
            self.surf = self.image_right
            self.rect.move_ip(self.speed, 0)
            self.move_collision_out(self.speed, 0)
        else:
            self.surf = self.image_left
            self.rect.move_ip(-self.speed, 0)
            self.move_collision_out(-self.speed, 0)


class Bird(Enemy):
    def __init__(self):
        super().__init__()
        self.engine.add_to_group(self, "birds")
        self.engine.add_to_group(self, "flammable")
        self.image_left = pygame.image.load(
            "images/bird_left.png"
        ).convert_alpha()
        self.image_right = pygame.image.load(
            "images/bird_right.png"
        ).convert_alpha()
        self.surf = self.image_left
        self.plant_bomb_count = 0

    def update(self):
        self.collisions_handling()
        self.move()
        if self.plant_bomb_count < 240:
            self.plant_bomb_count += 1
        elif self.plant_bomb_count == 240:
            self.plant_bomb()

    def plant_bomb(self):
        Bomb(self.rect.center)
        self.plant_bomb_count = 0

    def collisions_handling(self):
        player = self.engine.groups["player"].sprites()[0]
        if pygame.sprite.spritecollideany(self, self.engine.groups["player"]):
            player.change_health(-10)
            self.kill()
            Healing()
            Slow()
            Accelerate()

    def move(self):
        if self.rect.centerx > 0 and self.rect.centery > 0:
            self.surf = self.image_right
            self.rect.move_ip(-self.speed, -self.speed)


class Rock(EngineMovingSprite):
    def __init__(self, owner_center):
        super().__init__()
        self.engine.add_to_group(self, "rocks")
        self.engine.add_to_group(self, "flammable")
        self.surf = pygame.image.load("images/rock.png").convert_alpha()
        self.rect = self.surf.get_rect(
            center=self.get_self_center(owner_center)
        )

    def get_self_center(self, owner_center):
        lines = self.get_line_rock_placed(owner_center)
        return (
            lines[0] * DEFAULT_OBJ_SIZE + self.surf.get_width() // 2,
            lines[1] * DEFAULT_OBJ_SIZE + self.surf.get_height() // 2,
        )

    @staticmethod
    def get_line_rock_placed(owner_center):
        width = owner_center[0] // DEFAULT_OBJ_SIZE
        height = owner_center[1] // DEFAULT_OBJ_SIZE
        return width, height


class Effect(EngineMovingSprite, ABC):
    def __init__(self):
        super().__init__()
        self.position = self.generate_position()
        self.surf = pygame.Surface((20, 10))
        self.rect = self.surf.get_rect(center=self.position)

    def update(self):
        self.collisions_handling()

    @abstractmethod
    def collisions_handling(self):
        pass

    @staticmethod
    def generate_position() -> tuple:
        width = random.randint(0, SCREEN_WIDTH)
        height = random.randint(0, SCREEN_HEIGHT)
        return width, height


class Healing(Effect):
    def __init__(self):
        super().__init__()
        self.engine.add_to_group(self, "Healing")
        self.surf = pygame.image.load(
            "images/healing_effect.png").convert_alpha()

    def collisions_handling(self):
        player = self.engine.groups["player"].sprites()[0]
        if pygame.sprite.spritecollideany(self, self.engine.groups["player"]):
            player.change_health(200)
            self.kill()


class Slow(Effect):
    def __init__(self):
        super().__init__()
        self.engine.add_to_group(self, "slows")
        self.surf = pygame.image.load("images/slow_effect.png").convert_alpha()

    def collisions_handling(self):
        player = self.engine.groups["player"].sprites()[0]
        if pygame.sprite.spritecollideany(self, self.engine.groups["player"]):
            player.change_speed(-2)
            self.kill()


class Accelerate(Effect):
    def __init__(self):
        super().__init__()
        self.engine.add_to_group(self, "accelerates")
        self.surf = pygame.image.load("images/fast_effect.png").convert_alpha()

    def collisions_handling(self):
        player = self.engine.groups["player"].sprites()[0]
        if pygame.sprite.spritecollideany(self, self.engine.groups["player"]):
            player.change_speed(2)
            self.kill()
