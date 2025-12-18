import pygame
# ==========================================================
# == ANIMATION
# ==========================================================
class AnimatedSprite:
    def __init__(self, color=(0, 255, 0)):
        self.frames = [pygame.Surface((32, 32)) for _ in range(4)]
        for i, f in enumerate(self.frames):
            f.fill((color[0], color[1] - i * 40, color[2]))
        self.index = 0
        self.timer = 0
        self.image = self.frames[0]

    def update(self, dt):
        self.timer += dt
        if self.timer > 150:
            self.timer = 0
            self.index = (self.index + 1) % len(self.frames)
            self.image = self.frames[self.index]
