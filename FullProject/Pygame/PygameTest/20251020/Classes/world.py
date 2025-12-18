import pygame, math, random
from perlin_noise import PerlinNoise
from tile import Tile

MAP_WIDTH, MAP_HEIGHT = 150, 150
TILE_SIZE = 16

def generate_island():
    noise = PerlinNoise(octaves=4, seed=random.randint(0, 1000))
    temp_noise = PerlinNoise(octaves=3, seed=random.randint(0, 1000))
    world = []

    for y in range(MAP_HEIGHT):
        row = []
        for x in range(MAP_WIDTH):
            nx, ny = x / MAP_WIDTH - 0.5, y / MAP_HEIGHT - 0.5
            distance = math.sqrt(nx**2 + ny**2) / 0.7
            elevation = noise([nx * 2, ny * 2]) - distance * 0.8
            temperature = 300 + temp_noise([nx * 4, ny * 4]) * 20
            t = Tile(x, y, elevation, temperature)
            if t.height > 0.05 and random.random() < (t.height * 0.6):
                t.nature = random.randint(1, 5) if random.random() < 0.2 else random.randint(0, 3)
                t.update_visual_state()
            row.append(t)
        world.append(row)
    return world

def draw_world(surface, cam, world):
    for row in world:
        for tile in row:
            r = cam.apply(tile.rect)
            if cam.zoom < 0.4:
                continue
            surface.fill(tile.color, r)
