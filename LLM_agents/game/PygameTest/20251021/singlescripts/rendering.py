import pygame
import math
from config import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE



class Rendering:
    def __init__(self):
        pass # nothing to draw at creation




    def draw_non_player(self, surface, cam, world):
        vis_rect_world = pygame.Rect(cam.pos.x, cam.pos.y, WINDOW_WIDTH / cam.zoom, WINDOW_HEIGHT / cam.zoom)
        x0 = max(0, int(vis_rect_world.left // TILE_SIZE))
        y0 = max(0, int(vis_rect_world.top // TILE_SIZE))
        x1 = min(world.w, int(math.ceil(vis_rect_world.right / TILE_SIZE)))
        y1 = min(world.h, int(math.ceil(vis_rect_world.bottom / TILE_SIZE)))




        for y in range(y0, y1):
            row = world.tiles[y]
        for x in range(x0, x1):
            t = row[x]
            surface.fill(t.color, cam.apply(t.rect))