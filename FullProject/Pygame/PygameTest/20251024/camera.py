# -------------------- camera.py --------------------
import pygame, math
from config import WINDOW_WIDTH, WINDOW_HEIGHT, MAX_ZOOM_OUT, MIN_ZOOM_IN


class Camera:
    def __init__(self):
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.pos = pygame.Vector2(0, 0)


    def apply(self, rect):
        return pygame.Rect(
        int((rect.x - self.pos.x) * self.zoom),
        int((rect.y - self.pos.y) * self.zoom),
        math.ceil(rect.width * self.zoom),
        math.ceil(rect.height * self.zoom)
)

    def update(self, target_rect):
        self.target_zoom = max(MAX_ZOOM_OUT, min(MIN_ZOOM_IN, self.target_zoom))
        self.pos.x = target_rect.centerx - WINDOW_WIDTH / (2 * self.zoom)
        self.pos.y = target_rect.centery - WINDOW_HEIGHT / (2 * self.zoom)
        self.zoom += (self.target_zoom - self.zoom) * 0.1
