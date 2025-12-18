import pygame

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 720

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
