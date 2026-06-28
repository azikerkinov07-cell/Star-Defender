import pygame
import random
import sys
from pygame import mixer

# ====================== ИНИЦИАЛИЗАЦИЯ ======================
pygame.init()
mixer.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Star Defender")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)   # Новый шрифт для управления
big_font = pygame.font.Font(None, 72)

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)
CYAN = (50, 255, 255)

# ====================== ЗВУКИ ======================
try:
    shoot_sound = mixer.Sound("sounds/shoot.wav")
    explosion_sound = mixer.Sound("sounds/explosion.wav")
except:
    shoot_sound = explosion_sound = None

# ====================== КЛАССЫ (без изменений) ======================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, CYAN, [(25, 0), (0, 40), (50, 40)])
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 20
        self.speed = 8
        self.shoot_delay = 220
        self.last_shot = 0
        self.double_shot = False
        self.shield = False
        self.shield_time = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))

        if self.shield and pygame.time.get_ticks() - self.shield_time > 8000:
            self.shield = False

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullets.add(Bullet(self.rect.centerx, self.rect.top))
            if self.double_shot:
                bullets.add(Bullet(self.rect.centerx - 15, self.rect.top))
                bullets.add(Bullet(self.rect.centerx + 15, self.rect.top))
            if shoot_sound:
                shoot_sound.play()

    def draw_shield(self):
        if self.shield:
            pygame.draw.circle(screen, GREEN, self.rect.center, 35, 3)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 16))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -13

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type=0, is_boss=False):
        super().__init__()
        self.is_boss = is_boss
        self.type = enemy_type

        if is_boss:
            self.image = pygame.Surface((90, 70), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, (180, 0, 255), [(45, 0), (0, 70), (90, 70)])
            self.health = 18
            self.points = 2000
            self.speed = 3
        else:
            if enemy_type == 0: color = RED; self.health = 1; self.points = 100
            elif enemy_type == 1: color = (255, 140, 0); self.health = 1; self.points = 150
            else: color = (200, 0, 200); self.health = 3; self.points = 300
            self.image = pygame.Surface((45, 35), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, color, [(22, 0), (0, 35), (45, 35)])
            self.speed = random.randint(3, 7) if enemy_type != 2 else 2.5

        self.rect = self.image.get_rect()
        self.rect.x = random.randint(30, WIDTH - self.rect.width - 30)
        self.rect.y = -100 if not is_boss else -150

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            if explosion_sound: explosion_sound.play()
            create_explosion(self.rect.centerx, self.rect.centery, self.is_boss)
            self.kill()
            return self.points
        return 0


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.type = random.choice(["double", "shield", "speed"])
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        if self.type == "double": self.image.fill(YELLOW)
        elif self.type == "shield": self.image.fill(GREEN)
        else: self.image.fill(CYAN)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 4.5

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


class Particle:
    def __init__(self, x, y, big=False):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-6, 3)
        self.life = random.randint(25, 45) if big else random.randint(18, 35)
        self.color = random.choice([YELLOW, RED, WHITE, (255, 200, 0)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.25
        self.life -= 1

    def draw(self):
        if self.life > 0:
            alpha = int(255 * (self.life / 40))
            s = pygame.Surface((7, 7), pygame.SRCALPHA)
            s.fill((*self.color, alpha))
            screen.blit(s, (self.x, self.y))


# ====================== ГРУППЫ ======================
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()

player = Player()
all_sprites.add(player)
particles = []

stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)) for _ in range(160)]

def draw_background():
    screen.fill(BLACK)
    for i, (x, y, size) in enumerate(stars):
        pygame.draw.circle(screen, WHITE, (x, y), size)
        stars[i] = (x, (y + 2.5) % HEIGHT, size)

def create_explosion(x, y, big=False):
    count = 45 if big else 25
    for _ in range(count):
        particles.append(Particle(x, y, big))

# ====================== ПЕРЕМЕННЫЕ ======================
score = 0
level = 1
enemy_spawn_timer = 0
boss_spawned = False
game_state = "menu"

# ====================== ОСНОВНОЙ ЦИКЛ ======================
running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "menu":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game_state = "playing"
                    score = 0
                    level = 1
                    boss_spawned = False
                    for sprite in list(all_sprites):
                        if sprite != player: sprite.kill()
                    enemies.empty()
                    bullets.empty()
                    powerups.empty()
                    player.rect.centerx = WIDTH // 2
                    player.double_shot = False
                    player.shield = False
                elif event.key == pygame.K_q:
                    running = False

        elif game_state == "gameover":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game_state = "menu"

    if game_state == "playing":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            player.shoot()

        enemy_spawn_timer += 1
        spawn_rate = max(25, 75 - level * 5)

        if enemy_spawn_timer > spawn_rate:
            enemy_spawn_timer = 0
            if level % 5 == 0 and not boss_spawned:
                boss = Enemy(is_boss=True)
                all_sprites.add(boss)
                enemies.add(boss)
                boss_spawned = True
            else:
                etype = random.choices([0,1,2], weights=[45,35,20])[0]
                enemy = Enemy(etype)
                all_sprites.add(enemy)
                enemies.add(enemy)
                if random.random() < 0.14:
                    pu = PowerUp(enemy.rect.centerx, enemy.rect.centery)
                    all_sprites.add(pu)
                    powerups.add(pu)

        all_sprites.update()
        bullets.update()

        hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
        for enemy, _ in hits.items():
            points = enemy.hit()
            score += points
            if points > 0 and score // 1000 + 1 > level:
                level = min(level + 1, 15)

        if pygame.sprite.spritecollide(player, enemies, False):
            if not player.shield:
                create_explosion(player.rect.centerx, player.rect.centery, True)
                game_state = "gameover"

        for pu in pygame.sprite.spritecollide(player, powerups, True):
            if pu.type == "double":
                player.double_shot = True
                player.shoot_delay = 160
            elif pu.type == "shield":
                player.shield = True
                player.shield_time = pygame.time.get_ticks()
            else:
                player.speed = 11

    # ====================== ОТРИСОВКА ======================
    draw_background()
    all_sprites.draw(screen)

    for p in particles[:]:
        p.update()
        p.draw()
        if p.life <= 0:
            particles.remove(p)

    player.draw_shield()

    # HUD
    if game_state == "playing":
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        level_text = font.render(f"LEVEL: {level}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 50))

    elif game_state == "menu":
        # Заголовок
        title = big_font.render("STAR DEFENDER", True, CYAN)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        # Управление
        controls_title = font.render("CONTROLS", True, YELLOW)
        screen.blit(controls_title, (WIDTH//2 - controls_title.get_width()//2, 220))

        controls = [
            "← → or A D  -  Move",
            "SPACE (hold) - Shoot",
            "Collect Power-ups:",
            "   Yellow - Double Shot",
            "   Green  - Shield",
            "   Cyan   - Speed Boost"
        ]

        for i, line in enumerate(controls):
            text = small_font.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 260 + i * 32))

        # Кнопки действий
        start_text = font.render("PRESS ENTER TO START", True, WHITE)
        quit_text = font.render("PRESS Q TO QUIT", True, WHITE)
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, 480))
        screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, 520))

    elif game_state == "gameover":
        go_text = big_font.render("GAME OVER", True, RED)
        final_score = font.render(f"FINAL SCORE: {score}", True, WHITE)
        restart = font.render("PRESS R TO RETURN TO MENU", True, WHITE)
        screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, 180))
        screen.blit(final_score, (WIDTH//2 - final_score.get_width()//2, 270))
        screen.blit(restart, (WIDTH//2 - restart.get_width()//2, 320))

    pygame.display.flip()

pygame.quit()
sys.exit()