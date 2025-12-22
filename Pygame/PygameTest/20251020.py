# ==========================================================
# == Pygame Island Demo (Integrated, Option B)
# ==========================================================

import pygame
import random
import math
from perlin_noise import PerlinNoise

# ==========================================================
# == CONFIGURATION
# ==========================================================
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 720
TILE_SIZE = 16
MAP_WIDTH, MAP_HEIGHT = 150, 150
FPS = 60

pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()

# ==========================================================
# == CAMERA CLASS
# ==========================================================
class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.pos = pygame.Vector2(0, 0)

    def apply(self, rect):
        # integer rounding to remove seams
        return pygame.Rect(
            int((rect.x - self.pos.x) * self.zoom),
            int((rect.y - self.pos.y) * self.zoom),
            int(rect.width * self.zoom),
            int(rect.height * self.zoom),
        )

    def update(self, target_rect):
        self.pos.x = target_rect.centerx - WINDOW_WIDTH / (2 * self.zoom)
        self.pos.y = target_rect.centery - WINDOW_HEIGHT / (2 * self.zoom)
        self.zoom += (self.target_zoom - self.zoom) * 0.12

# ==========================================================
# == PLAYER CLASS
# ==========================================================
class Player:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], TILE_SIZE, TILE_SIZE)
        self.color = (200, 40, 40)
        self.speed = 220

    def handle_input(self, keys, joystick=None):
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]: move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x += 1

        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            if abs(axis_x) > 0.2 or abs(axis_y) > 0.2:
                move.x = axis_x
                move.y = axis_y
            print(f"[Joystick Debug] Axis X: {axis_x:.2f}, Axis Y: {axis_y:.2f}")

        if move.length_squared() > 0:
            move = move.normalize()
        return move

    def update(self, dt, move, obstacles):
        vel = move * self.speed * dt / 1000.0
        # Swept-AABB collisions
        self.rect = self.swept_aabb(vel, obstacles)

    def swept_aabb(self, velocity, obstacles):
        new_rect = self.rect.copy()
        new_rect.x += velocity.x
        for obs in obstacles:
            if new_rect.colliderect(obs):
                if velocity.x > 0: new_rect.right = obs.left
                elif velocity.x < 0: new_rect.left = obs.right
        new_rect.y += velocity.y
        for obs in obstacles:
            if new_rect.colliderect(obs):
                if velocity.y > 0: new_rect.bottom = obs.top
                elif velocity.y < 0: new_rect.top = obs.bottom
        return new_rect

    def draw(self, surf, cam):
        pygame.draw.rect(surf, self.color, cam.apply(self.rect))

# ==========================================================
# == MAP GENERATOR CLASS
# ==========================================================
class WorldMap:
    def __init__(self):
        self.layers = {"water":[], "grass":[], "trees":[], "temperature":{}, "obstacles":[]}
        self.noise = PerlinNoise(octaves=4, seed=random.randint(0,99999))
        self.generate()

    def generate(self):
        scale = 3.0 / min(MAP_WIDTH, MAP_HEIGHT)
        cx, cy = MAP_WIDTH/2, MAP_HEIGHT/2
        radius = min(MAP_WIDTH, MAP_HEIGHT) * 0.45
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                nx, ny = x*scale, y*scale
                e = self.noise([nx, ny])
                dist = math.hypot(x-cx, y-cy)/radius
                value = e - dist
                r = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                temp = random.uniform(270, 320)
                self.layers['temperature'][(x,y)] = temp
                if value < -0.05:
                    self.layers['water'].append(r)
                elif value < 0.15:
                    self.layers['grass'].append(r)
                    if random.random()<0.04:
                        self.layers['trees'].append(r.copy())
                        self.layers['obstacles'].append(r.copy())
                else:
                    self.layers['trees'].append(r.copy())
                    self.layers['obstacles'].append(r.copy())

    def draw(self, surf, cam):
        # Only draw tiles that are visible to camera (culling)
        visible_rect = pygame.Rect(cam.pos.x, cam.pos.y, WINDOW_WIDTH/cam.zoom, WINDOW_HEIGHT/cam.zoom)
        for name in ['water','grass','trees']:
            color = {'water':(10,40,160),'grass':(68,170,68),'trees':(16,90,16)}[name]
            for r in self.layers[name]:
                if r.colliderect(visible_rect):
                    surf.fill(color, cam.apply(r))

# ==========================================================
# == PLAYER WORLD INTERACTION
# ==========================================================
def interact(player, layers, action):
    px, py = int(player.rect.centerx//TILE_SIZE), int(player.rect.centery//TILE_SIZE)
    key = (px, py)
    if action == "plant":
        rect = pygame.Rect(px*TILE_SIZE, py*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        if rect not in layers['trees']:
            layers['trees'].append(rect)
            layers['obstacles'].append(rect)
            print(f"Planted tree at {key}")
    elif action == "cut":
        for tree in layers['trees']:
            if tree.collidepoint(player.rect.center):
                layers['trees'].remove(tree)
                if tree in layers['obstacles']: layers['obstacles'].remove(tree)
                print(f"Cut tree at {key}")
                break
    elif action == "heat":
        if key in layers['temperature']:
            layers['temperature'][key] += 5
            if layers['temperature'][key] > 330:
                layers['trees'] = [t for t in layers['trees'] if not t.collidepoint(player.rect.center)]
                layers['obstacles'] = [t for t in layers['obstacles'] if not t.collidepoint(player.rect.center)]
                print(f"🔥 Tree burned at {key}")

# ==========================================================
# == MINIMAP FUNCTION
# ==========================================================
def draw_minimap(surf, player, layers):
    mm_w, mm_h = 200, 100
    minimap = pygame.Surface((mm_w, mm_h))
    minimap.fill((10,10,30))
    for name in ['water','grass','trees']:
        color = {'water':(10,40,160),'grass':(68,170,68),'trees':(16,90,16)}[name]
        for r in layers[name]:
            x = int(r.x * mm_w / (MAP_WIDTH*TILE_SIZE))
            y = int(r.y * mm_h / (MAP_HEIGHT*TILE_SIZE))
            minimap.fill(color, (x, y, 2, 2))
    px = int(player.rect.centerx*mm_w/(MAP_WIDTH*TILE_SIZE))
    py = int(player.rect.centery*mm_h/(MAP_HEIGHT*TILE_SIZE))
    pygame.draw.circle(minimap, (255,50,50), (px, py), 3)
    surf.blit(minimap, (10, WINDOW_HEIGHT-mm_h-10))

# ==========================================================
# == MAIN LOOP
# ==========================================================
player = Player((MAP_WIDTH*TILE_SIZE//2, MAP_HEIGHT*TILE_SIZE//2))
cam = Camera()
world = WorldMap()

joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for js in joysticks: js.init()

running = True
action = None
frame_times = []
perf_timer = 0
max_frame_time = 0
PERF_INTERVAL = 3.0

while running:
    dt = clock.tick(FPS)
    perf_timer += dt/1000.0
    frame_times.append(dt)
    if dt > max_frame_time: max_frame_time = dt

    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: action = "plant"
            elif event.key == pygame.K_2: action = "cut"
            elif event.key == pygame.K_3: action = "heat"
        elif event.type == pygame.MOUSEWHEEL:
            cam.target_zoom *= 1.0 + event.y*0.1

    joystick = joysticks[0] if joysticks else None
    move = player.handle_input(keys, joystick)
    player.update(dt, move, world.layers['obstacles'])
    cam.update(player.rect)

    if action:
        interact(player, world.layers, action)
        action = None

    window.fill((8,10,30))
    world.draw(window, cam)
    player.draw(window, cam)
    draw_minimap(window, player, world.layers)
    pygame.display.flip()

    if perf_timer >= PERF_INTERVAL:
        print(f"[Performance Spike] max frame time in last {PERF_INTERVAL}s: {max_frame_time:.2f} ms")
        perf_timer = 0
        max_frame_time = 0

pygame.quit()
