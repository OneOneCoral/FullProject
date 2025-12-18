# ==========================================================
# == Pygame Island Demo with Camera, Swept-AABB, Joystick, and Layers
# ==========================================================

import pygame
import random
import math



# ==========================================================
# == UTILITIES
# ==========================================================
def clamp(v, minv, maxv):
    return max(minv, min(maxv, v))


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
        # no zoom limit for full-map view
        self.zoom += (self.target_zoom - self.zoom) * 0.1


# ==========================================================
# == PHYSICS (Swept-AABB)
# ==========================================================
def swept_aabb(moving, velocity, obstacles):
    new_rect = moving.copy()
    new_rect.x += velocity.x
    for obs in obstacles:
        if new_rect.colliderect(obs):
            if velocity.x > 0:
                new_rect.right = obs.left
            elif velocity.x < 0:
                new_rect.left = obs.right
    new_rect.y += velocity.y
    for obs in obstacles:
        if new_rect.colliderect(obs):
            if velocity.y > 0:
                new_rect.bottom = obs.top
            elif velocity.y < 0:
                new_rect.top = obs.bottom
    return new_rect

# ==========================================================
# == MAP GENERATION
# ==========================================================

class World_map_generator():
# should this also have an argument for changes that have been made of the map? map stage? or is there a map gnereator and then a saved map?
    def __init__(self, Mapkeygneration):
        self.value = random()

    # for the map i would love different valuse for sertain sets of info: so that the temperature, how wet the tile is, the stade of the solit sand stone metal and if there is any foliage growth grass tree bush tall gras usW.
    def generate_map(MAP_WIDTH=100, MAP_HEIGHT=100, TILE_SIZE=16):
        layers = {
            "liquid": [],
            "solid": [],
            "Temp-in-Kelvin": [],
            "air-pressure": [],
            "nature": [],
            "buildings": [],
        }

        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                dist = math.hypot(x - MAP_WIDTH / 2, y - MAP_HEIGHT / 2)
                if dist < 35:
                    layers["liquid"] = 100



                if layers["liquid"] > 50:
                    layers["liquid"].append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                elif dist > 35:
                    layers["solid"].append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                else:
                    layers["nature"].append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))
                    if random.random() < 0.05:
                        layers["trees"].append(pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

                # Example: generate extra data values
                temp = random.uniform(250, 320)  # Kelvin
                pressure = random.uniform(95000, 105000)  # Pascals

                layers["Temp-in-Kelvin"].append(temp)
                layers["air-pressure"].append(pressure)

        return layers


# ==========================================================
# == MAIN LOOP
# ==========================================================
player = Player((MAP_WIDTH * TILE_SIZE / 2, MAP_HEIGHT * TILE_SIZE / 2))
cam = Camera()
layers = World_map_generator.generate_map()
obstacles = layers["trees"]
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for js in joysticks:
    js.init()

running = True
while running:
    dt = clock.tick(60)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEWHEEL:
            cam.target_zoom *= 1.0 + event.y * 0.1

    joystick = joysticks[0] if joysticks else None
    move = player.handle_input(keys, joystick)
    player.update(dt, move, obstacles)
    cam.update(player.rect)

    window.fill((0, 0, 50))

    # Draw layers should this not better be a render map function so that the code is cleaner? or is there a specific use why this should go in the main game loop? should there be a seperate rendering call?
    # ok so what I would like is for the map to be drawn based of valuse of the  generate_map   function (so this part would be the (skinns/sprites) part then?) so I would like it to draw water if the value for water is larger than 1 tress when nature value 3 or higher usw. feel free to take folow up steps to increase enviorment diversety
    for name, rects in layers.items():
        color = {
            "liquid": (0, 0, 180),
            "solid": (200, 180, 50),
            "nature": (0, 180, 0),

        }[name]
        for r in rects:
            window.fill(color, cam.apply(r))

    player.draw(window, cam)
    pygame.display.flip()

pygame.quit()
