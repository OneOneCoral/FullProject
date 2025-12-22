import pygame
import sys
import random


pygame.init()
def clamp_rect(rect, bounds_w, bounds_h):
    if rect.width > bounds_w:
        rect.width = bounds_w
    if rect.height > bounds_h:
        rect.height = bounds_h
    if rect.left < 0:
        rect.left = 0
    if rect.top < 0:
        rect.top = 0
    if rect.right > bounds_w:
        rect.left = bounds_w - rect.width
    if rect.bottom > bounds_h:
        rect.top = bounds_h - rect.height
    return rect


def random_colour():
    return (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))

def generate_chunk(CHUNK_SIZE_x, CHUNK_SIZE_y):
    """Generate a chunk surface for chunk coordinates (cx, cy)."""
    surf = pygame.Surface((CHUNK_SIZE_x, CHUNK_SIZE_y))
    surf.fill(random_colour())
    return surf

def generate_random_colure_rect(surface, x_size,y_size, x_position, y_position):
    pygame.draw.rect((surface), random_colour(), (x_position, y_position,x_size, y_size))

# ---------- World_and_maps ----------

CHUNK_SIZE = 256
WORLD_CHUNKS_X = 12
WORLD_CHUNKS_Y = 9
VIRTUAL_WIDTH = CHUNK_SIZE * WORLD_CHUNKS_X
VIRTUAL_HEIGHT = CHUNK_SIZE * WORLD_CHUNKS_Y

# ---------- CONFIG ----------
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 720   # real window (what the player sees)
HUD_WIDTH, HUD_HEIGHT = 100, 200         # an off-screen HUD surface (example)

# ---------- SETUP ----------
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Zoomable Virtual Surface Demo (1200x720)")

FPS = 60
PLAYER_SPEED = 300.0  # pixels / second in virtual coordinates
PLAYER_SIZE = 28

# Zoom settings
zoom = 1.0
ZOOM_MIN, ZOOM_MAX = 0.5, 3.0
ZOOM_STEP = 1.15  # multiply / divide

# Off-screen surfaces
game_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
hud_surface = pygame.Surface((HUD_WIDTH, HUD_HEIGHT), pygame.SRCALPHA)

# Player state (in virtual coordinates)
player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
player_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)

clock = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    # ---------- EVENTS ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mouse wheel zoom (works on many platforms)
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                zoom *= ZOOM_STEP
            else:
                zoom /= ZOOM_STEP
            zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom))


    # Movement input (virtual coordinates)
    keys = pygame.key.get_pressed()
    move = pygame.Vector2(0, 0)
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        move.x = -1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        move.x = 1
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        move.y = -1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        move.y = 1
    if move.length_squared() > 0:
        move = move.normalize()

    player_pos += move * PLAYER_SPEED * dt

    # clamp player inside virtual world
    player_pos.x = max(0 + PLAYER_SIZE/2, min(VIRTUAL_WIDTH - PLAYER_SIZE/2, player_pos.x))
    player_pos.y = max(0 + PLAYER_SIZE/2, min(VIRTUAL_HEIGHT - PLAYER_SIZE/2, player_pos.y))

    # ---------- RENDER TO OFF-SCREEN SURFACES ----------
    # Draw game world

    game_surface.fill((20, 24, 30))  # background

    # simple grid for orientation
    grid_color = (40, 45, 60)
    grid_spacing = 40
    for x in range(0, VIRTUAL_WIDTH, grid_spacing):
        pygame.draw.line(game_surface, grid_color, (x, 0), (x, VIRTUAL_HEIGHT))
    for y in range(0, VIRTUAL_HEIGHT, grid_spacing):
        pygame.draw.line(game_surface, grid_color, (0, y), (VIRTUAL_WIDTH, y))


    # def generate_level_element_circle():

    # draw some level elements (example)
    generate_random_colure_rect(game_surface, 50, 50, 100, 100)
    generate_random_colure_rect(game_surface, 200, 200, 1000, 1000)

    pygame.draw.circle(game_surface, (200, 120, 80), (VIRTUAL_WIDTH - 80, VIRTUAL_HEIGHT - 60), 40)

    # draw player (virtual coords)
    player_rect.center = (int(player_pos.x), int(player_pos.y))
    pygame.draw.rect(game_surface, (200, 40, 40), player_rect)

    # Draw HUD (off-screen)
    hud_surface.fill((0, 0, 0, 0))  # keep transparent background
    pygame.draw.rect(hud_surface, (10, 10, 10, 200), (0, 0, 100, 100))  # semi-transparent box
    font = pygame.font.SysFont(None, 24)
    hud_surface.blit(font.render(f"Zoom: {zoom:.2f}x", True, (255, 255, 255)), (10, 10))
    hud_surface.blit(font.render(f"Player: ({int(player_pos.x)},{int(player_pos.y)})", True, (255, 255, 255)), (10, 35))

    # ---------- CAMERA / ZOOM ----------
    # We want to capture a rectangle of the game world centered on the player, whose size depends on zoom.
    # If zoom == 1.0, we capture WORLD rect of size (WINDOW_WIDTH, WINDOW_HEIGHT) in world coords.
    # If zoom > 1.0, we capture a smaller world rect, which gets scaled up to WINDOW.
    desired_world_w = max(1, int(WINDOW_WIDTH / zoom))
    desired_world_h = max(1, int(WINDOW_HEIGHT / zoom))

    world_rect = pygame.Rect(
        int(player_pos.x - desired_world_w / 2),
        int(player_pos.y - desired_world_h / 2),
        desired_world_w,
        desired_world_h
    )
    # clamp to the virtual world's bounds so we don't go out of range
    world_rect = clamp_rect(world_rect, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

    # Blit portion of game_surface into a temporary surface and scale it to window size
    temp = pygame.Surface((world_rect.width, world_rect.height))
    temp.blit(game_surface, (0, 0), area=world_rect)
    scaled_game = pygame.transform.smoothscale(temp, (WINDOW_WIDTH, WINDOW_HEIGHT))

    # Final compose: blit scaled game to the real screen
    screen.blit(scaled_game, (0, 0))

    # Scale/position HUD as desired (example: top-right corner)
    hud_target_w, hud_target_h = 360, 120  # on-screen size of HUD
    scaled_hud = pygame.transform.smoothscale(hud_surface, (hud_target_w, hud_target_h))
    screen.blit(scaled_hud, (WINDOW_WIDTH - hud_target_w - 10, 10))

    # Optional: draw a small minimap of virtual world in the corner (not scaled by camera)
    minimap_w, minimap_h = 200, 100
    minimap = pygame.transform.smoothscale(game_surface, (minimap_w, minimap_h))
    # draw player on minimap (approx)
    player_on_minimap_x = int(player_pos.x * minimap_w / VIRTUAL_WIDTH)
    player_on_minimap_y = int(player_pos.y * minimap_h / VIRTUAL_HEIGHT)
    pygame.draw.circle(minimap, (255, 50, 50), (player_on_minimap_x, player_on_minimap_y), 4)
    screen.blit(minimap, (10, WINDOW_HEIGHT - minimap_h - 10))

    # ---------- FINISH FRAME ----------
    pygame.display.flip()

pygame.quit()
sys.exit()
