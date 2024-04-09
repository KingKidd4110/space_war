import os
import pygame
import math

os.chdir(os.path.dirname(os.path.abspath(__file__)))

MAX_AREA = 30000  # 50000
BULLET_DAMAGE = 1
GUN_TIME = 8
BULLET_START_POS = pygame.Vector2(4, 0)
BULLET_SPEED = 40
BULLET_LIFE = 100
FUEL_USAGE_ACCELERATION = 1
FUEL_USAGE_TURN = 0.1

SHIP_SCALE = 4
GUN_POSITIONS = [
    [pygame.Vector2(6, 4), pygame.Vector2(6, -4)],
    [pygame.Vector2(4, 4), pygame.Vector2(4, -4), pygame.Vector2(19, 0)],
    [pygame.Vector2(4, 4), pygame.Vector2(4, -4), pygame.Vector2(19, 0)],
    [
        pygame.Vector2(4, 4),
        pygame.Vector2(4, -4),
        pygame.Vector2(19, 0),
        pygame.Vector2(8, 7),
        pygame.Vector2(8, -7),
    ],
    [
        pygame.Vector2(4, 4),
        pygame.Vector2(4, -4),
        pygame.Vector2(19, 0),
        pygame.Vector2(8, 7),
        pygame.Vector2(8, -7),
        pygame.Vector2(2, 10),
        pygame.Vector2(2, -10),
    ],
]

GUN_UPGRADE_MULTIPLIERS = 80  # (bullet_speed, bullet_life)
LEVEL_INFO = [
    (3, 3, 1),
    (3, 3, 1),
    (5, 5, 2),
    (5, 5, 2),
    (7, 5, 2),
]  # (bodies, rockets, turning_rockets)


def level_info_multiplier(info, multiplier):
    return lambda level: LEVEL_INFO[level][info] * multiplier


rocket_power = level_info_multiplier(1, 0.1)
ammo_storage = level_info_multiplier(0, 250)
turning_rocket_power = level_info_multiplier(2, 3)
health = level_info_multiplier(0, 20)
ship_damage = level_info_multiplier(0, 30)
fuel_storage = level_info_multiplier(0, 1250)


def clamp(n, min_n, max_n):
    return min(max(n, min_n), max_n)


def import_image(image_name, scale):
    image = pygame.image.load(image_name).convert_alpha()
    target_size = (int(image.get_width() * scale), int(image.get_height() * scale))
    return pygame.transform.scale(image, target_size)


def dir_dis_to_xy(direction, distance):
    return pygame.Vector2(
        (distance * math.cos(math.radians(direction))),
        -(distance * math.sin(math.radians(direction))),
    )


def xy_to_dir_dis(xy):
    return math.degrees(math.atan2(xy.y, xy.x)), math.sqrt(
        (0 - xy.x) ** 2 + (0 - xy.y) ** 2
    )


class Thing:
    def __init__(self, image, spawn_pos=pygame.Vector2(0), spawn_direction=0):
        self.image = image
        self.pos = spawn_pos
        self.direction = spawn_direction
        self.size = pygame.Vector2(0)
        self.draw_pos = pygame.Vector2(0)
        self.rot_center()

    def draw(self, screen, pos=None, offset=pygame.Vector2(0)):
        self.rot_center(pos=pos)
        screen.blit(self.rotated_image, self.draw_pos + offset)

    def rot_center(self, pos=None):
        self.rotated_image = pygame.transform.rotate(self.image, self.direction)
        if pos != None:
            self.rect = self.rotated_image.get_rect(center=pos)
        else:
            self.rect = self.rotated_image.get_rect(center=self.pos)
        self.size.update(self.rect.size)
        self.draw_pos.update(self.rect.topleft)
        self.mask = pygame.mask.from_surface(self.rotated_image)

    def object_mask_collision(self, other):
        pos = (other.pos - self.pos) - ((other.size / 2) - (self.size / 2))
        return bool(self.mask.overlap_area(other.mask, (int(pos.x), int(pos.y))))


class Bullet(Thing):
    def __init__(self, image, spawn_pos, direction, speed, time_alive):
        super().__init__(image, spawn_pos, direction)
        self.velocity = dir_dis_to_xy(self.direction, speed)
        self.time_alive = time_alive

    def update(self):
        self.pos += self.velocity
        self.time_alive -= 1


class Spaceship(Thing):
    def __init__(self, images, level, spawn_pos=pygame.Vector2(0), spawn_direction=0):
        super().__init__(images[level], spawn_pos, spawn_direction)
        self.level = level
        self.images = images
        self.level_to_stats()

        self.fire_rate = 0
        self.gun_timer = 0

        self.acceleration = 0
        self.velocity = pygame.Vector2(0)
        self.turn = 0

        self.ammo = self.max_ammo
        self.health = self.max_health
        self.fuel = self.max_fuel

    def level_to_stats(self):
        self.image = self.images[self.level]
        self.rocket_power = rocket_power(self.level)
        self.max_ammo = ammo_storage(self.level)
        self.turning_power = turning_rocket_power(self.level)
        self.max_health = health(self.level)
        self.ship_damage = ship_damage(self.level)
        self.bullet_speed = BULLET_SPEED
        self.bullet_life = BULLET_LIFE
        self.guns_activated = self.level
        self.max_fuel = fuel_storage(self.level)

    def update(self):
        fuel_usage = (abs(self.turn) * FUEL_USAGE_TURN) + (
            self.acceleration * FUEL_USAGE_ACCELERATION
        )
        if self.fuel - fuel_usage >= 0:
            self.fuel -= fuel_usage
            self.direction += self.turn
            self.velocity += dir_dis_to_xy(self.direction, self.acceleration)
        self.pos += self.velocity

        bullets_to_spawn = []

        self.gun_timer += self.fire_rate
        if self.gun_timer >= GUN_TIME:
            self.gun_timer = 0

            for gun_pos in GUN_POSITIONS[self.guns_activated]:
                if self.ammo:
                    self.ammo -= 1
                    direction, distance = xy_to_dir_dis(
                        (gun_pos * SHIP_SCALE) + BULLET_START_POS
                    )
                    bullets_to_spawn.append(
                        Bullet(
                            bullet_image,
                            self.pos
                            + dir_dis_to_xy(direction + self.direction, distance),
                            self.direction,
                            self.bullet_speed,
                            self.bullet_life,
                        )
                    )

        return bullets_to_spawn

    def control(self, acceleration, turn_amount, fire_rate, guns_activated=None):
        self.turn = clamp(turn_amount, -self.turning_power, self.turning_power)
        self.acceleration = clamp(acceleration, 0, self.rocket_power)
        self.fire_rate = clamp(fire_rate, 0, 1)
        if guns_activated != None:
            if guns_activated <= self.level:
                self.guns_activated = guns_activated


spaceship_images = [
    import_image(image_name, SHIP_SCALE)
    for image_name in [
        "rocket_stage1.png",
        "rocket_stage2.png",
        "rocket_stage3.png",
        "rocket_stage4.png",
        "rocket_stage5.png",
    ]
]
enemy_spaceship_images = [
    import_image(image_name, SHIP_SCALE)
    for image_name in [
        "enemy_stage1.png",
        "enemy_stage2.png",
        "enemy_stage3.png",
        "enemy_stage4.png",
        "enemy_stage5.png",
    ]
]
bullet_image = import_image("bullet.png", int(SHIP_SCALE / 2))