import pygame
from config import MAP_WIDTH, MAP_HEIGHT, TILE_SIZE
from world import World

# Instantiate the world so minimap has data
world = World(MAP_WIDTH, MAP_HEIGHT)

class MiniMap:
    def __init__(self, world_ref, width=300, height=300):
        self.world = world_ref
        self.width = width
        self.height = height
        self.surface = None

    def create_mini_map(self):
        """Builds a minimap surface from current world tile colors."""
        mini = pygame.Surface((self.world.w, self.world.h))
        for y in range(self.world.h):
            for x in range(self.world.w):
                tile = self.world.tiles[y][x]
                mini.set_at((x, y), tile.color)
        # store scaled map for later reuse
        self.surface = pygame.transform.scale(mini, (self.width, self.height))

    def draw(self, window, pos=(10, 10)):
        """Draws the minimap if available."""
        if self.surface:
            window.blit(self.surface, pos)
