# ==========================================================
# == game Island World Optimized (Tile Simulation, Zoom, Performance Profiling)
# ==========================================================
import pygame, random, math, time
from perlin_noise import PerlinNoise

# ==========================================================
# == CONFIGURATION
# ==========================================================
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 720
TILE_SIZE = 16
MAP_WIDTH, MAP_HEIGHT = 150, 150
FPS = 60

HEAT_DIFFUSE_RATE = 0.10
WATER_DIFFUSE_RATE = 0.18
EVAP_PER_K = 0.00012
WATER_COOLING = 0.04
REGROWTH_RATE = 0.005
DECAY_RATE = 0.01
TREE_THRESHOLD = 4.0

VILLAGE_COUNT = 8
NPCS_PER_VILLAGE = 8
VILLAGE_RADIUS_TILES = 12

MAX_ZOOM_OUT = 1

MIN_ZOOM_IN = 3.5

UPDATE_STEP_LIMIT = 6000  # number of tiles to process per frame (performance cap)
clock = pygame.time.Clock()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
# ==========================================================
# == CAMERA
# ==========================================================
class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.pos = pygame.Vector2(0, 0)

    def apply(self, rect):
        # integer rounding removes seams
        return pygame.Rect(
            int((rect.x - self.pos.x) * self.zoom),
            int((rect.y - self.pos.y) * self.zoom),
            math.ceil(rect.width * self.zoom),
            math.ceil(rect.height * self.zoom)
        )

    def update(self, target_rect):
        # limit zoom
        self.target_zoom = max(MAX_ZOOM_OUT, min(MIN_ZOOM_IN, self.target_zoom))
        self.pos.x = target_rect.centerx - WINDOW_WIDTH / (2 * self.zoom)
        self.pos.y = target_rect.centery - WINDOW_HEIGHT / (2 * self.zoom)
        self.zoom += (self.target_zoom - self.zoom) * 0.1

# ==========================================================
# == TILE
# ==========================================================
class Tile:
    __slots__ = ("x", "y", "rect", "water", "earth", "nature", "heat", "color", "is_obstacle")
    def __init__(self, x, y, height, temp):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.water = max(0.0, min(1.0, 1.0 - (height + 0.25)*1.2)) if height < 0.5 else 0.0
        self.earth = max(0.0, min(1.0, 1.0 - self.water))
        self.nature = 0.0
        self.heat = float(temp)
        self.is_obstacle = False
        self.update_visual()

    def fertile(self):
        return (0.22 <= self.water <= 0.65) and (285 <= self.heat <= 315) and (self.earth > 0.3)

    def harsh(self):
        return (self.water < 0.12) or (self.heat >= 330) or (self.earth < 0.2)

    def update_visual(self):
        self.is_obstacle = self.nature >= TREE_THRESHOLD
        if self.water > 0.68:
            self.color = (0, 0, 160)
        elif self.water > 0.38:
            self.color = (20, 100, 200)
        else:
            if self.nature >= 4.5:
                self.color = (0, 70, 0)
            elif self.nature >= 3.5:
                self.color = (10, 115, 10)
            elif self.nature >= 2.0:
                self.color = (60, 170, 60)
            elif self.nature >= 1.0:
                self.color = (105, 200, 105)
            else:
                base = int(170 + (self.heat - 300) * 0.35)
                base = max(100, min(230, base))
                self.color = (base, base - 20, 80)

# ==========================================================
# == WORLD
# ==========================================================
class World:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.tiles = [[None]*w for _ in range(h)]
        self._gen_island()
        self._seed_vegetation()
        self._update_index = 0

    def _gen_island(self):
        elev_noise = PerlinNoise(octaves=4, seed=random.randint(0, 99999))
        temp_noise = PerlinNoise(octaves=3, seed=random.randint(0, 99999))
        for y in range(self.h):
            for x in range(self.w):
                nx, ny = x/self.w - 0.5, y/self.h - 0.5
                dist = math.sqrt(nx*nx + ny*ny) / 0.72
                height = elev_noise([nx*2.3, ny*2.3]) - dist*0.85
                temp = 300 + temp_noise([nx*3.1, ny*3.1]) * 18
                self.tiles[y][x] = Tile(x, y, height, temp)

    def _seed_vegetation(self):
        for row in self.tiles:
            for t in row:
                if t.water < 0.3 and t.earth > 0.4:
                    t.nature = random.uniform(0.0, 2.2)
                if t.fertile() and random.random() < 0.10:
                    t.nature = max(t.nature, random.uniform(1.0, 3.5))
                if t.fertile() and random.random() < 0.03:
                    t.nature = max(t.nature, random.uniform(4.0, 5.0))
                t.update_visual()

    def simulate_step(self, budget):
        total_tiles = self.w * self.h
        steps = 0
        while steps < budget and self._update_index < total_tiles:
            y, x = divmod(self._update_index, self.w)
            self._update_tile(x, y)
            self._update_index += 1
            steps += 1
        if self._update_index >= total_tiles:
            self._update_index = 0

    def _update_tile(self, x, y):
        t = self.tiles[y][x]
        neigh = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0: continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    neigh.append(self.tiles[ny][nx])
        if not neigh: return

        avg_heat = sum(nb.heat for nb in neigh)/len(neigh)
        avg_water = sum(nb.water for nb in neigh)/len(neigh)

        t.heat += (avg_heat - t.heat) * HEAT_DIFFUSE_RATE - WATER_COOLING * avg_water
        t.water += (avg_water - t.water) * WATER_DIFFUSE_RATE - max(0.0, (t.heat - 300) * EVAP_PER_K)
        t.water = max(0.0, min(1.0, t.water))
        t.earth = 1.0 - t.water

        if t.fertile():
            t.nature = min(5.0, t.nature + REGROWTH_RATE)
        if t.harsh():
            t.nature = max(0.0, t.nature - DECAY_RATE)
        if t.heat > 335 and t.nature >= 3.0:
            t.nature = max(0.0, t.nature - 0.05)

        t.update_visual()

# ==========================================================
# == PLAYER
# ==========================================================
class Player:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], TILE_SIZE, TILE_SIZE)
        self.speed = 220
        self.color = (220, 60, 60)

    def handle_input(self, keys):
        v = pygame.Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        )
        if v.length_squared(): v = v.normalize()
        return v

    def update(self, dt_ms, move, world, cam):
        # Speed scales inversely with zoom so movement slows as you zoom in
        zoom_factor = cam.zoom
        actual_speed = self.speed / zoom_factor
        dx = int(move.x * actual_speed * dt_ms / 1000.0)
        dy = int(move.y * actual_speed * dt_ms / 1000.0)
        self.rect.x += dx
        self.rect.y += dy

    def draw(self, surf, cam):
        pygame.draw.rect(surf, self.color, cam.apply(self.rect))

# ==========================================================
# == DRAW
# ==========================================================
def draw_world(surface, cam, world):
    vis_rect_world = pygame.Rect(cam.pos.x, cam.pos.y, WINDOW_WIDTH/cam.zoom, WINDOW_HEIGHT/cam.zoom)
    x0 = max(0, int(vis_rect_world.left // TILE_SIZE))
    y0 = max(0, int(vis_rect_world.top // TILE_SIZE))
    x1 = min(world.w, int(math.ceil(vis_rect_world.right / TILE_SIZE)))
    y1 = min(world.h, int(math.ceil(vis_rect_world.bottom / TILE_SIZE)))

    for y in range(y0, y1):
        row = world.tiles[y]
        for x in range(x0, x1):
            t = row[x]
            surface.fill(t.color, cam.apply(t.rect))

# ==========================================================
# == MAIN
# ==========================================================
player = Player((MAP_WIDTH*TILE_SIZE//2, MAP_HEIGHT*TILE_SIZE//2))
cam = Camera()
world = World(MAP_WIDTH, MAP_HEIGHT)

running = True
perf_timer, max_spike = 0.0, 0.0

while running:
    start = time.time()
    dt = clock.tick(FPS)
    perf_timer += dt / 1000.0

    keys = pygame.key.get_pressed()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEWHEEL:
            cam.target_zoom *= 1.0 + e.y * 0.1

    move = player.handle_input(keys)
    player.update(dt, move, world, cam)
    cam.update(player.rect)

    # update only a set number of tiles per frame
    world.simulate_step(UPDATE_STEP_LIMIT)

    window.fill((10, 10, 30))
    draw_world(window, cam, world)
    player.draw(window, cam)

    pygame.display.flip()

    frame_ms = (time.time() - start) * 1000
    max_spike = max(max_spike, frame_ms)

    if perf_timer >= 3.0:
        print(f"[Performance Spike] Max frame in last 3s: {max_spike:.2f} ms")
        max_spike = 0.0
        perf_timer = 0.0

pygame.quit()
