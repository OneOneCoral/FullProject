import pygame
TILE_SIZE = 16

class Tile:
    def __init__(self, x, y, height, temp):
        self.x, self.y = x, y
        self.height = height
        self.heat = temp
        self.nature = 0
        self.water = max(0.0, 1 - height * 1.5) if height < 0.5 else 0.0
        self.earth = 1 - self.water
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.update_visual_state()

    def update_visual_state(self):
        if self.water > 0.6:
            self.color = (0, 0, 180)
        elif self.water > 0.3:
            self.color = (20, 100, 200)
        elif self.nature > 4:
            self.color = (0, 80, 0)
        elif self.nature > 3:
            self.color = (20, 150, 20)
        elif self.nature > 2:
            self.color = (40, 180, 40)
        elif self.nature > 1:
            self.color = (60, 200, 60)
        else:
            self.color = (180, 160, 80)

    def step(self):
        pass
