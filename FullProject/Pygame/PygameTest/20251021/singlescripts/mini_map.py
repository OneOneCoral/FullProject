import pygame
from config import  MAP_WIDTH
from config import MAP_HEIGHT
from config import TILE_SIZE

class MINI_MAP():
    def __init__ (self):
        pass

    def build_minimap_surface(self, layers, w=MAP_WIDTH, h=MAP_HEIGHT):
        mini = pygame.Surface((w, h))
        # draw at 1:1 per tile, then we'll scale to on-screen size
        mini.fill((0, 0, 0))
        for r in layers["water"]:
            mini.fill((0, 0, 150), (r.x // TILE_SIZE, r.y // TILE_SIZE, 1, 1))
        for r in layers["grass"]:
            mini.fill((60, 180, 60), (r.x // TILE_SIZE, r.y // TILE_SIZE, 1, 1))
        for r in layers["trees"]:
            mini.fill((10, 100, 10), (r.x // TILE_SIZE, r.y // TILE_SIZE, 1, 1))
        return mini