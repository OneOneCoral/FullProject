# ==========================================================
# == game Island World (Organic Tile System)
# ==========================================================
import pygame, random, math
from perlin_noise import PerlinNoise

# ==========================================================
# == CONFIGURATION
# ==========================================================
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 720
TILE_SIZE = 16
MAP_WIDTH, MAP_HEIGHT = 150, 150

pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()

# ==========================================================
# == CAMERA
# ==========================================================
class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.pos = pygame.Vector2(0, 0)

    def apply(self, rect):
        return pygame.Rect(
            (rect.x - self.pos.x) * self.zoom,
            (rect.y - self.pos.y) * self.zoom,
            rect.width * self.zoom,
            rect.height * self.zoom,
        )

    def update(self, target_rect):
        self.pos.x = target_rect.centerx - WINDOW_WIDTH / (2 * self.zoom)
        self.pos.y = target_rect.centery - WINDOW_HEIGHT / (2 * self.zoom)
        self.zoom += (self.target_zoom - self.zoom) * 0.1

# ==========================================================
# == TILE STRUCTURE
# ==========================================================
class Tile:
    def __init__(self, x, y, height, temp):
        self.x, self.y = x, y
        self.height = height          # Determines if water/land/mountain
        self.heat = temp              # Heat level 250–350 (Kelvin)
        self.nature = 0               # 0–5 for vegetation
        self.water = max(0.0, 1 - height * 1.5) if height < 0.5 else 0.0
        self.earth = 1 - self.water
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.update_visual_state()

    def update_visual_state(self):
        """Choose color/sprite based on values."""
        if self.water > 0.6:
            self.color = (0, 0, 180)
        elif self.water > 0.3:
            self.color = (20, 100, 200)
        elif self.nature > 4:
            self.color = (0, 80, 0)     # Tree
        elif self.nature > 3:
            self.color = (20, 150, 20)  # Bush
        elif self.nature > 2:
            self.color = (40, 180, 40)  # Tall grass
        elif self.nature > 1:
            self.color = (60, 200, 60)  # Grass
        else:
            self.color = (180, 160, 80) # Bare earth

    def step(self):
        """Simple environment logic (for Step B later)."""
        pass

# ==========================================================
# == PLAYER
# ==========================================================
class Player:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], 16, 16)
        self.color = (0, 255, 0)
        self.speed = 200

    def handle_input(self, keys):
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w]: move.y -= 1
        if keys[pygame.K_s]: move.y += 1
        if keys[pygame.K_a]: move.x -= 1
        if keys[pygame.K_d]: move.x += 1
        if move.length_squared() > 0:
            move = move.normalize()
        return move

    def update(self, dt, move):
        vel = move * self.speed * dt / 1000.0
        self.rect.x += vel.x
        self.rect.y += vel.y

    def draw(self, surf, cam):
        r = cam.apply(self.rect)
        pygame.draw.rect(surf, self.color, r)

# ==========================================================
# == MAP GENERATION
# ==========================================================
def generate_island():
    noise = PerlinNoise(octaves=4, seed=random.randint(0, 1000))
    temp_noise = PerlinNoise(octaves=3, seed=random.randint(0, 1000))
    world = []

    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            nx, ny = x / MAP_WIDTH - 0.5, y / MAP_HEIGHT - 0.5
            distance = math.sqrt(nx**2 + ny**2) / 0.7  # round island shape
            elevation = noise([nx * 2, ny * 2]) - distance * 0.8
            temperature = 300 + temp_noise([nx * 4, ny * 4]) * 20
            t = Tile(x, y, elevation, temperature)

            # Populate vegetation only on land
            if t.height > 0.05 and random.random() < (t.height * 0.6):
                t.nature = random.randint(1, 5) if random.random() < 0.2 else random.randint(0, 3)
                t.update_visual_state()

            row.append(t)
        world.append(row)
    return world

# ==========================================================
# == DRAW WORLD
# ==========================================================
def draw_world(surface, cam, world):
    for row in world:
        for tile in row:
            r = cam.apply(tile.rect)
            if cam.zoom < 0.4:  # Performance: skip tiny tiles
                continue
            surface.fill(tile.color, r)

# ==========================================================
# == MAIN LOOP
# ==========================================================
player = Player((MAP_WIDTH*TILE_SIZE/2, MAP_HEIGHT*TILE_SIZE/2))
cam = Camera()
world = generate_island()

running = True
while running:
    dt = clock.tick(60)
    keys = pygame.key.get_pressed()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEWHEEL:
            cam.target_zoom *= 1.0 + e.y * 0.1

    move = player.handle_input(keys)
    player.update(dt, move)
    cam.update(player.rect)

    window.fill((10, 10, 30))
    draw_world(window, cam, world)
    player.draw(window, cam)
    pygame.display.flip()

pygame.quit()
