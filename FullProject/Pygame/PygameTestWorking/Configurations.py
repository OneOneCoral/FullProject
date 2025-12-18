import pygame

# ==========================================================
# == CONFIGURATION
# ==========================================================
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 720
TILE_SIZE = 32
MAP_WIDTH, MAP_HEIGHT = 100, 100

pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
