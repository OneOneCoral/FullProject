import pygame
from camera import Camera
from world import generate_island, draw_world

WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 720
TILE_SIZE = 16
MAP_WIDTH, MAP_HEIGHT = 150, 150

pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()

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
