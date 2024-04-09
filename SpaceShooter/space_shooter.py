import pygame
import os
import random
import pygame
import math
from win32api import GetSystemMetrics

os.chdir(os.path.dirname(os.path.abspath(__file__)))

TITLE = "Space Shooter"
sys_met = tuple(map(GetSystemMetrics, (0, 1)))
SIZE = (sys_met[0], sys_met[1] - 60)  # (1000, 600)


def turn_to_angle(angle, turn_to_angle):
    turn = -(angle - turn_to_angle)

    while turn > 180:
        turn -= 360
    while turn < -180:
        turn += 360

    return turn


def stars_gen(density, min_size, max_size, star_image, size):
    result = pygame.Surface(size, flags=pygame.SRCALPHA).convert_alpha()
    star_width, star_height = star_image.get_size()
    for x in range(0, int(size.x)):
        for y in range(0, int(size.y)):
            if random.random() < density:
                scale = random.uniform(min_size, max_size)
                blit_star = pygame.transform.scale(
                    star_image, (int(star_width * scale), int(star_height * scale))
                )
                result.blit(blit_star, (x, y))
    return result


class Label:
    def __init__(self, pos, size, color, text, text_color):
        self.font = pygame.font.SysFont("monospace", 15)
        self.rect = pygame.Rect(pos, size)
        self.text_color = text_color
        self.color = color
        self.image = pygame.Surface(size).convert_alpha()
        self.image.fill(self.color)
        text_image = self.font.render(text, 1, self.text_color).convert_alpha()
        text_rect = text_image.get_rect(
            center=pygame.math.Vector2(self.image.get_size()) / 2
        )
        self.image.blit(text_image, text_rect)

    def draw(self, win):
        win.blit(self.image, self.rect)


class button(Label):
    def __init__(self, pos, size, color, text, text_color):
        super().__init__(pos, size, color, text, text_color)

    def is_hovered_over(self, point):
        return self.rect.collidepoint(point)


class Stat(Label):
    def __init__(self, pos, size, color, text, text_color):
        super().__init__(pos, size, color, text, text_color)

    def update_text(self, new_text):
        text_image = self.font.render(new_text, 1, self.text_color).convert_alpha()
        self.image.fill(self.color)
        text_rect = text_image.get_rect(
            center=pygame.math.Vector2(self.image.get_size()) / 2
        )
        self.image.blit(text_image, text_rect)


class InfoBar:
    def __init__(self, pos, size, bar_color, background_color, start_value=1):
        self.pos = pos
        self.size = size
        self.value = start_value
        self.background_color = background_color
        self.bar_color = bar_color
        self.image = pygame.Surface(size).convert_alpha()
        self.bar = pygame.Surface(size).convert_alpha()
        self.bar.fill(self.bar_color)
        self.update_value(new_value=start_value)

    def update_value(self, change_value_by=0, new_value=0):
        if change_value_by:
            self.value += change_value_by
        else:
            self.value = new_value
        self.image.fill(self.background_color)
        self.image.blit(self.bar, (-self.value * self.size.x, 0))

    def draw(self, win):
        win.blit(self.image, self.pos)


class space:
    def __init__(self, space_image, screen, pos):
        self.screen = screen
        self.space_image = space_image

    def update(self, pos):
        screen_size = pygame.Vector2(self.screen.get_size())
        pos = pygame.Vector2((pos.x % screen_size.x), (pos.y % screen_size.y))

        scroll_surf = pygame.Surface(screen_size).convert_alpha()
        scroll_surf.blit(self.space_image, pos)
        if pos.x > 0:
            scroll_surf.blit(self.space_image, pos - pygame.Vector2(screen_size.x, 0))
        else:
            scroll_surf.blit(self.space_image, pos + pygame.Vector2(screen_size.x, 0))
        if pos.y > 0:
            scroll_surf.blit(self.space_image, pos - pygame.Vector2(0, screen_size.y))
        else:
            scroll_surf.blit(self.space_image, pos + pygame.Vector2(0, screen_size.y))
        if pos.x > 0 and pos.y > 0:
            scroll_surf.blit(
                self.space_image, pos - pygame.Vector2(screen_size.x, screen_size.y)
            )
        self.screen.blit(scroll_surf, (0, 0))


def handle_events():
    spaceships_to_delete = []
    for n, spaceship in enumerate(spaceships):
        if n == player:
            if spaceship.health <= 0:
                return True
        else:
            if spaceship.health <= 0:
                spaceships_to_delete.append(n)
                spaceships[player].xp += 1
                if (
                    spaceships[player].health + spaceships[player].max_health / 5
                    < spaceships[player].max_health
                ):
                    spaceships[player].health += spaceships[player].max_health / 5
                values = [
                    getattr(spaceships[player], r_t[1])
                    / getattr(spaceships[player], r_t[0])
                    for r_t in player_reward_types
                ]
                reward_type = player_reward_types[values.index(min(values))]
                max_value = getattr(spaceships[player], reward_type[0])
                to_add = getattr(spaceships[player], reward_type[1]) + (max_value / 5)
                before = getattr(spaceships[player], reward_type[1])
                if to_add < max_value:
                    setattr(spaceships[player], reward_type[1], to_add)
                    after = getattr(spaceships[player], reward_type[1])
                    print("+", after - before, reward_type[1])

    spaceships_to_delete.reverse()
    for n in spaceships_to_delete:
        spaceships.pop(n)
    if (
        spaceships[player].level != 4
        and spaceships[player].xp > ((spaceships[player].level + 1) * 4) - 1
    ):
        spaceships[player].xp = 0
        spaceships[player].level += 1
        spaceships[player].level_to_stats()
    if spaceships[player].xp < (spaceships[player].level + 1) * 4:
        for n in spaceships_to_delete:
            spaceships.append(
                things.Spaceship(
                    things.enemy_spaceship_images,
                    spaceships[player].level,
                    spawn_pos=pygame.Vector2(
                        random.randrange(
                            int(-things.MAX_AREA), int(things.MAX_AREA), 1000
                        ),
                        random.randrange(
                            int(-things.MAX_AREA), int(things.MAX_AREA), 1000
                        ),
                    ),
                    spawn_direction=random.randrange(0, 360),
                )
            )
            if len(spaceships) < 40:
                spaceships.append(
                    things.Spaceship(
                        things.enemy_spaceship_images,
                        spaceships[player].level,
                        spawn_pos=pygame.Vector2(
                            random.randrange(
                                int(-things.MAX_AREA), int(things.MAX_AREA), 1000
                            ),
                            random.randrange(
                                int(-things.MAX_AREA), int(things.MAX_AREA), 1000
                            ),
                        ),
                        spawn_direction=random.randrange(0, 360),
                    )
                )

    bullets_to_delete = []
    for n, bullet in enumerate(bullets):
        if bullet.time_alive <= 0:
            bullets_to_delete.append(n)
    bullets_to_delete.reverse()
    for n in bullets_to_delete:
        bullets.pop(n)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        # if event.type == pygame.KEYDOWN:
        # if event.key == pygame.K_q:
        #    spaceships[1].health = 0
        # if event.key == pygame.K_q:
        #    spaceships[player].level -= 1
        #    spaceships[player].level_to_stats()
        # if event.key == pygame.K_e:
        #    spaceships[player].level += 1
        #    spaceships[player].level_to_stats()

    left, middle, right = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    mouse_dir = -things.xy_to_dir_dis(
        mouse_pos - pygame.Vector2(spaceships[player].rect.center)
    )[0]

    acceleration = 0
    turn_amount = 0
    fire_rate = 0
    guns_activated = None

    if left:
        acceleration = spaceships[player].rocket_power
    if right:
        fire_rate = 1
    turn_amount = turn_to_angle(spaceships[player].direction, mouse_dir)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_1]:
        guns_activated = 0
    if keys[pygame.K_2]:
        guns_activated = 1
    if keys[pygame.K_3]:
        guns_activated = 3
    if keys[pygame.K_4]:
        guns_activated = 4

    # print((turn_to_angle(mouse_dir, spaceship.direction)), (turn_to_angle(head_to, spaceship.direction))+spaceship.direction, head_to, spaceship.direction)
    spaceships[player].control(
        acceleration, turn_amount, fire_rate, guns_activated=guns_activated
    )

    for spaceship in spaceships:
        if spaceship != spaceships[player]:
            head_to = 0
            acceleration = 0
            fire_rate = 0
            distance = things.xy_to_dir_dis(spaceships[player].pos - spaceship.pos)[1]
            if distance < 10000:
                if things.xy_to_dir_dis(
                    spaceship.velocity
                    + things.dir_dis_to_xy(spaceship.direction, spaceship.rocket_power)
                )[1] < (((spaceship.level + 3) / 3) * 8):
                    acceleration = spaceship.rocket_power
                else:
                    acceleration = 0
                head_to = -things.xy_to_dir_dis(spaceship.pos - spaceships[player].pos)[
                    0
                ]
                if distance < 2000:
                    fire_rate = 0.3
                spaceship.control(
                    acceleration, turn_to_angle(head_to, spaceship.direction), fire_rate
                )
            else:
                if (
                    things.xy_to_dir_dis(
                        spaceship.velocity
                        + things.dir_dis_to_xy(
                            spaceship.direction, spaceship.rocket_power
                        )
                    )[1]
                    < 5
                ):
                    acceleration = spaceship.rocket_power / 10
                head_to = -things.xy_to_dir_dis(spaceship.pos)[0]
                # print((turn_to_angle(head_to, spaceship.direction)), (turn_to_angle(head_to, spaceship.direction))+spaceship.direction, head_to, spaceship.direction)
                # print(spaceship.direction)
                spaceship.control(
                    acceleration,
                    (turn_to_angle(head_to, spaceship.direction) / 100),
                    fire_rate,
                )
                # print(spaceship.direction)

    return False


def draw():
    mini_map.fill((0, 0, 0))

    follow = player
    draw_offset = (-spaceships[follow].pos) + win_center
    space_background.update(draw_offset)
    for n, spaceship in enumerate(spaceships):
        mini_map_spaceship_pos = ((spaceship.pos / mini_map_size) / 2) + mini_map_middle
        if n == follow:
            spaceship.draw(screen, pos=win_center)
            mini_map.blit(mini_map_dots["player"], mini_map_spaceship_pos)
        else:
            spaceship.draw(screen, offset=(draw_offset))
            mini_map.blit(mini_map_dots["enemy"], mini_map_spaceship_pos)

    for bullet in bullets:
        bullet.draw(screen, offset=(draw_offset))

    for label in labels:
        label.draw(screen)
    for label, bar in info_bars.values():
        label.draw(screen)
        bar.draw(screen)
    for label, text in info_text.values():
        label.draw(screen)
        text.draw(screen)

    screen.blit(mini_map, mini_map_draw_pos)


def game_logic():
    for bullet in bullets:
        bullet.update()

        if (
            bullet.pos.x > things.MAX_AREA
            or bullet.pos.x < -things.MAX_AREA
            or bullet.pos.y > things.MAX_AREA
            or bullet.pos.y < -things.MAX_AREA
        ):
            bullet.time_alive = 0
            continue
        for spaceship in spaceships:
            if bullet.object_mask_collision(spaceship):
                spaceship.health -= things.BULLET_DAMAGE
                bullet.time_alive = 0

    for n, spaceship in enumerate(spaceships):
        for bullet in spaceship.update():
            bullets.append(bullet)

        if (
            spaceship.pos.x > things.MAX_AREA
            or spaceship.pos.x < -things.MAX_AREA
            or spaceship.pos.y > things.MAX_AREA
            or spaceship.pos.y < -things.MAX_AREA
        ):
            spaceship.health = 0

    for n, spaceship in enumerate(spaceships):
        collide_checks = spaceships.copy()
        collide_checks.pop(n)

        for other in collide_checks:
            if spaceship.object_mask_collision(other):
                spaceship.health -= other.ship_damage

    info_bars["ammo"][1].update_value(
        new_value=(-(spaceships[player].ammo / spaceships[player].max_ammo)) + 1
    )
    info_bars["health"][1].update_value(
        new_value=(-(spaceships[player].health / spaceships[player].max_health)) + 1
    )
    info_bars["fuel"][1].update_value(
        new_value=(-(spaceships[player].fuel / spaceships[player].max_fuel)) + 1
    )
    info_text["speed"][1].update_text(
        str(int(things.xy_to_dir_dis(spaceships[player].velocity)[1]))
    )
    info_text["pos"][1].update_text(
        str((int(spaceships[player].pos.x), int(spaceships[player].pos.y)))
    )
    info_text["guns activated"][1].update_text(
        str(spaceships[player].guns_activated + 1)
    )
    info_text["ship level"][1].update_text(str(spaceships[player].level + 1))
    info_text["xp"][1].update_text(str(spaceships[player].xp))


def run_game():
    while True:
        if handle_events():
            break

        game_logic()
        draw()

        pygame.display.update(window_rect)
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode(SIZE)
    import things

    mini_map_size = 200
    mini_map_middle = (
        pygame.Vector2(things.MAX_AREA, things.MAX_AREA) / mini_map_size
    ) / 2
    mini_map = pygame.Surface(
        pygame.Vector2(things.MAX_AREA, things.MAX_AREA) / mini_map_size
    ).convert_alpha()
    mini_map_dots = {
        "player": pygame.Surface(pygame.Vector2(1, 1)).convert_alpha(),
        "enemy": pygame.Surface(pygame.Vector2(1, 1)).convert_alpha(),
    }
    mini_map_dots["player"].fill((0, 200, 0))
    mini_map_dots["enemy"].fill((200, 0, 0))
    mini_map_draw_pos = pygame.Vector2(10, 10)
    window_rect = pygame.Rect((0, 0), SIZE)
    win_center = pygame.Vector2(window_rect.center)
    clock = pygame.time.Clock()
    pygame.display.set_caption(TITLE)
    pygame.event.set_allowed([pygame.KEYDOWN, pygame.QUIT])

    stars = pygame.Surface(pygame.Vector2(screen.get_size())).convert_alpha()
    stars.fill((10, 10, 13))
    stars.blit(
        stars_gen(
            0.0001,
            0.4,
            0.9,
            things.import_image("star.png", 1),
            pygame.Vector2(screen.get_size()),
        ),
        (0, 0),
    )
    space_background = space(stars, screen, pygame.Vector2(0))

    bullets = []
    player = 0
    spaceships = [
        things.Spaceship(things.spaceship_images, 0, spawn_pos=pygame.Vector2(0, 0))
    ]
    spaceships.append(
        things.Spaceship(
            things.enemy_spaceship_images,
            spaceships[player].level,
            spawn_pos=pygame.Vector2(
                random.randrange(int(-things.MAX_AREA), int(things.MAX_AREA), 1000),
                random.randrange(int(-things.MAX_AREA), int(things.MAX_AREA), 1000),
            ),
            spawn_direction=random.randrange(0, 360),
        )
    )
    # for x in range(int(-things.MAX_AREA), int(things.MAX_AREA), 1000):
    # for y in range(int(-things.MAX_AREA), int(things.MAX_AREA), 1000):
    # if random.random() < 0.002:
    # spaceships.append(things.Spaceship(things.enemy_spaceship_images,
    # spaceships[player].level,
    # spawn_pos=pygame.Vector2(x, y),
    # spawn_direction=random.randrange(0, 360)))

    player_reward_types = (
        ("max_health", "health"),
        ("max_ammo", "ammo"),
        ("max_fuel", "fuel"),
    )
    spaceships[player].xp = 0

    # (label, info_bar)
    info_bars = {
        "ammo": (
            Label(
                pygame.Vector2(SIZE[0] - 90, SIZE[1] - 65),
                pygame.Vector2(60, 16),
                (200, 200, 200),
                "ammo",
                (20, 20, 20),
            ),
            InfoBar(
                pygame.Vector2(SIZE[0] - 100, SIZE[1] - 40),
                pygame.Vector2(80, 20),
                (0, 0, 100),
                (100, 100, 100),
                0,
            ),
        ),
        "health": (
            Label(
                pygame.Vector2(SIZE[0] - 90, SIZE[1] - 125),
                pygame.Vector2(60, 16),
                (200, 200, 200),
                "health",
                (20, 20, 20),
            ),
            InfoBar(
                pygame.Vector2(SIZE[0] - 100, SIZE[1] - 100),
                pygame.Vector2(80, 20),
                (0, 0, 100),
                (100, 100, 100),
                0,
            ),
        ),
        "fuel": (
            Label(
                pygame.Vector2(SIZE[0] - 90, SIZE[1] - 185),
                pygame.Vector2(60, 16),
                (200, 200, 200),
                "fuel",
                (20, 20, 20),
            ),
            InfoBar(
                pygame.Vector2(SIZE[0] - 100, SIZE[1] - 160),
                pygame.Vector2(80, 20),
                (0, 0, 100),
                (100, 100, 100),
                0,
            ),
        ),
    }
    # (label, info_text)
    info_text = {
        "speed": (
            Label(
                pygame.Vector2(SIZE[0] - 90, SIZE[1] - 245),
                pygame.Vector2(60, 16),
                (200, 200, 200),
                "speed",
                (20, 20, 20),
            ),
            Stat(
                pygame.Vector2(SIZE[0] - 90, SIZE[1] - 220),
                pygame.Vector2(60, 20),
                (200, 200, 200),
                "0",
                (20, 20, 20),
            ),
        ),
        "pos": (
            Label(
                pygame.Vector2(70, SIZE[1] - 65),
                pygame.Vector2(60, 16),
                (200, 200, 200),
                "pos",
                (20, 20, 20),
            ),
            Stat(
                pygame.Vector2(20, SIZE[1] - 40),
                pygame.Vector2(160, 20),
                (200, 200, 200),
                "(0, 0)",
                (20, 20, 20),
            ),
        ),
        "guns activated": (
            Label(
                pygame.Vector2(30, SIZE[1] - 125),
                pygame.Vector2(140, 16),
                (200, 200, 200),
                "guns activated",
                (20, 20, 20),
            ),
            Stat(
                pygame.Vector2(70, SIZE[1] - 100),
                pygame.Vector2(60, 20),
                (200, 200, 200),
                "0",
                (20, 20, 20),
            ),
        ),
        "ship level": (
            Label(
                pygame.Vector2(50, SIZE[1] - 185),
                pygame.Vector2(100, 16),
                (200, 200, 200),
                "ship level",
                (20, 20, 20),
            ),
            Stat(
                pygame.Vector2(70, SIZE[1] - 160),
                pygame.Vector2(60, 20),
                (200, 200, 200),
                "0",
                (20, 20, 20),
            ),
        ),
        "xp": (
            Label(
                pygame.Vector2(SIZE[0] - 90, SIZE[1] - 305),
                pygame.Vector2(60, 16),
                (200, 200, 200),
                "xp",
                (20, 20, 20),
            ),
            Stat(
                pygame.Vector2(SIZE[0] - 90, SIZE[1] - 280),
                pygame.Vector2(60, 20),
                (200, 200, 200),
                "0",
                (20, 20, 20),
            ),
        ),
    }
    labels = (
        []
    )  # Label(pygame.Vector2(0, 0), pygame.Vector2(60, 20), (200, 200, 200), "hi", (20, 20, 20))]

    run_game()