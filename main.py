import pygame
import math
import time
import random
from PIL import Image, ImageFilter

pygame.mixer.init()
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("shooter!!!!11!11")

clock = pygame.time.Clock()

glow_image = pygame.transform.scale(pygame.image.load("images/glow.png").convert_alpha(), (50, 50))

font = pygame.font.Font("fonts/font.otf", 60)
font_big = pygame.font.Font("fonts/font.otf", 120)
font_italic = pygame.font.Font("fonts/font_italic.otf", 20)

def normalize(v: tuple[float, float]):
    l = math.sqrt(v[0]*v[0] + v[1]*v[1])
    return (v[0] / l, v[1] / l)

def mult(v: tuple[float, float], multiplier: float):
    return (v[0] * multiplier, v[1] * multiplier)

class Game:
    def __init__(self):
        self.objects = []
        self.players: list[Player] = []

        self.enemy_spawn_cooldown = 0
        self.enemy_spawn_time = time.time()

    def run(self, surface: pygame.Surface) -> bool:
        return_false = False
        screen.fill((31, 31, 31))
        if time.time() - self.enemy_spawn_time > self.enemy_spawn_cooldown:
            enemy = Enemy(random.randint(0, screen.get_width()), random.randint(0, screen.get_height()), self.players[0])
            enemy.spawn()
            self.objects.append(enemy)
            self.enemy_spawn_cooldown = random.random()
            self.enemy_spawn_time = time.time()

        for obj in self.objects:
            obj.draw(surface)
            if not obj.update(): return_false = True

        if self.players[0].dash_cooldown > 0:
            surface.blit(font_italic.render("DASH COOLDOWN", True, (255, 255, 255)), (20, 20))
            pygame.draw.polygon(surface, (15, 15, 15), [(20, 75), (50, 50), (230, 50), (200, 75)])
            x = 200 * (self.players[0].dash_cooldown / 300)
            pygame.draw.polygon(surface, (255, 15, 255), [(20, 75), (50, 50), (x + 50, 50), (x + 20, 75)])
        
        score_len = len(str(self.players[0].score))
        for i, char in enumerate(str(self.players[0].score)):
            score_surface = font.render(char, True, (255, 255, 255))
            rect = score_surface.get_rect(center=(surface.get_width() // 2 + (i - 0.5 * score_len) * 35, 60 + 5 * math.sin(2 * time.time() + i)))
            surface.blit(score_surface, rect)
        if return_false: return False
        return True

class Player:
    def __init__(self, x, y):
        self.x, self.y = (x, y)
        self.vx, self.vy = (0, 0)
        self.keys = [False for _ in range(256)]
        self.fire_cooldown = 0
        self.dash_cooldown = 0
        self.score = 0
        self.game = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN: self.keys[event.key] = True
        if event.type == pygame.KEYUP: self.keys[event.key] = False     

    def update(self) -> bool:
        if self.keys[pygame.K_w]: self.vy -= 1
        if self.keys[pygame.K_a]: self.vx -= 1
        if self.keys[pygame.K_s]: self.vy += 1
        if self.keys[pygame.K_d]: self.vx += 1

        self.fire_cooldown -= 1
        self.dash_cooldown -= 1

        if self.keys[pygame.K_SPACE] and self.dash_cooldown < 1:
            mouse_pos = pygame.mouse.get_pos()
            self.vx, self.vy = mult(normalize((mouse_pos[0] - self.x, mouse_pos[1] - self.y)), 50)
            self.dash_cooldown = 300

        self.vx *= 0.9
        self.vy *= 0.9

        self.x += self.vx
        self.y += self.vy
        
        if self.x > screen.get_width() - 25:
            self.x = screen.get_width() - 25
            self.vx *= -1
        if self.x < 25:
            self.x = 25
            self.vx *= -1
        if self.y > screen.get_height() - 25: 
            self.y = screen.get_height() - 25
            self.vy *= -1
        if self.y < 25:
            self.y = 25
            self.vy *= -1

        if pygame.mouse.get_pressed()[0] and self.fire_cooldown < 1:
            mouse_pos = pygame.mouse.get_pos()
            fire_dir = normalize((mouse_pos[0] - self.x, mouse_pos[1] - self.y))
            speed = 10
            Bullet(self.x, self.y, speed * fire_dir[0], speed * fire_dir[1]).add_to_game(self.game)

            self.fire_cooldown = 5

        for entity in self.game.objects:
            if isinstance(entity, Enemy) and pygame.Rect((self.x - 25, self.y - 25, 50, 50)).colliderect(pygame.Rect((entity.x - 25, entity.y - 25, 50, 50))):
                return False
            
        return True


    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, (255, 255, 255), (self.x - 25, self.y - 25, 50, 50))

    def add_to_game(self, game: Game):
        self.game = game
        game.objects.append(self)
        game.players.append(self)
        return self

class Enemy:
    def __init__(self, x, y, target: Player):
        self.x, self.y = (x, y)
        self.vx, self.vy = (0, 0)
        self.target = target

    def update(self) -> bool:
        self.vx, self.vy = mult(normalize((self.target.x - self.x, self.target.y - self.y)), 5)

        self.x += self.vx
        self.y += self.vy
        return True

    def spawn(self):
        diff_x, diff_y = (self.target.x - self.x, self.target.y - self.y)
        while math.sqrt(diff_x * diff_x + diff_y * diff_y) < 400: 
            self.x = random.randint(0, screen.get_width())
            self.y = random.randint(0, screen.get_height())
            diff_x, diff_y = (self.target.x - self.x, self.target.y - self.y)

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, (255, 0, 0), (self.x - 25, self.y - 25, 50, 50))

class Bullet:
    def __init__(self, x, y, vx, vy):
        self.x, self.y = (x, y)
        self.vx, self.vy = (vx, vy)
        self.game: Game = None

    def draw(self, surface: pygame.Surface):
        screen.blit(glow_image, (self.x - 20, self.y - 20))
        pygame.draw.rect(surface, (255, 0, 0), (self.x, self.y, 10, 10))
    
    def update(self) -> bool:
        if self.x > screen.get_width() or self.x < 0 or \
           self.y > screen.get_height() or self.y < 0:
            self.game.objects.remove(self)
            del self
            return True

        self.x += self.vx
        self.y += self.vy

        for entity in self.game.objects:
            entity_rect = pygame.Rect(entity.x - 25, entity.y - 25, 50, 50)
            if isinstance(entity, Bullet | Player): continue
            if pygame.Rect((self.x, self.y, 10, 10)).colliderect(entity_rect):
                pygame.mixer.music.load("sounds/hit.wav")
                pygame.mixer.music.play()
                self.game.objects.remove(entity)
                self.game.objects.remove(self)
                self.game.players[0].score += 1
                del self
                return True
        return True

    def add_to_game(self, game: Game):
        self.game = game
        game.objects.append(self)
        return self

game: Game = Game()
player: Player = Player(500, 500).add_to_game(game)

while True:
    while game.run(screen):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP: player.handle_event(event)
        
        clock.tick(60)
        pygame.display.flip()
    
    pygame.mixer.music.load("sounds/die.wav")
    pygame.mixer.music.play()
    dimensions = (screen.get_size()[0] // 2, screen.get_size()[1] // 2)
    image: Image = Image.frombytes("RGB", dimensions, pygame.image.tobytes(pygame.transform.scale(screen, dimensions), "RGB"))
    radius = 0

    letter = font_big.render("g", True, (255, 255, 255))

    while True:
        blurred: Image = image.filter(ImageFilter.GaussianBlur(radius))
        bg = pygame.transform.scale(pygame.image.frombytes(blurred.tobytes(), dimensions, "RGB"), screen.get_size())
        screen.blit(bg, (0, 0))
        screen.blit(letter, letter.get_rect(center=(screen.get_size()[0] // 2 - 50, 100 + 10 * math.sin(2 * time.time()))))
        screen.blit(letter, letter.get_rect(center=(screen.get_size()[0] // 2 + 30, 100 + 10 * math.sin(2 * time.time() + 1))))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP: player.handle_event(event)
        
        radius += 0.0625 * (20 - radius)
        clock.tick(60)
        pygame.display.flip()