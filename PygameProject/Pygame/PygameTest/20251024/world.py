import pygame, random, math, time
from perlin_noise import PerlinNoise
from config import TILE_SIZE, TREE_THRESHOLD, HEAT_DIFFUSE_RATE, WATER_DIFFUSE_RATE, WATER_COOLING, DECAY_RATE, REGROWTH_RATE, EVAP_PER_K
from tiles import Tile
import config

# ==========================================================
# == WORLD
# ==========================================================


class World:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.tiles = [[None]*w for _ in range(h)]
        self._gen_island()
        self._seed_vegetation()
        self._update_index = 0

    def _gen_island(self):
        elev_noise = PerlinNoise(octaves=4, seed=random.randint(0, 99999))
        temp_noise = PerlinNoise(octaves=3, seed=random.randint(0, 99999))
        for y in range(self.h):
            for x in range(self.w):
                nx, ny = x/self.w - 0.5, y/self.h - 0.5
                dist = math.sqrt(nx*nx + ny*ny) / 0.72
                height = elev_noise([nx*2.3, ny*2.3]) - dist*0.85
                temp = 300 + temp_noise([nx*3.1, ny*3.1]) * 18
                self.tiles[y][x] = Tile(x, y, height, temp)

    def _seed_vegetation(self):
        for row in self.tiles:
            for t in row:
                if t.water < 0.3 and t.earth > 0.4:
                    t.nature = random.uniform(0.0, 2.2)
                if t.fertile() and random.random() < 0.10:
                    t.nature = max(t.nature, random.uniform(1.0, 3.5))
                if t.fertile() and random.random() < 0.03:
                    t.nature = max(t.nature, random.uniform(4.0, 5.0))
                t.update_visual()

    def simulate_step(self, budget):
        total_tiles = self.w * self.h
        steps = 0
        while steps < budget and self._update_index < total_tiles:
            y, x = divmod(self._update_index, self.w)
            self._update_tile(x, y)
            self._update_index += 1
            steps += 1
        if self._update_index >= total_tiles:
            self._update_index = 0





    def _update_tile(self, x, y):
        t = self.tiles[y][x]
        neigh = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0: continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    neigh.append(self.tiles[ny][nx])
        if not neigh: return

        avg_heat = sum(nb.heat for nb in neigh)/len(neigh)
        avg_water = sum(nb.water for nb in neigh)/len(neigh)

        t.heat += (avg_heat - t.heat) * HEAT_DIFFUSE_RATE - WATER_COOLING * avg_water
        t.water += (avg_water - t.water) * WATER_DIFFUSE_RATE - max(0.0, (t.heat - 300) * EVAP_PER_K)
        t.water = max(0.0, min(1.0, t.water))
        t.earth = 1.0 - t.water

        if t.fertile():
            t.nature = min(5.0, t.nature + REGROWTH_RATE)
        if t.harsh():
            t.nature = max(0.0, t.nature - DECAY_RATE)
        if t.heat > 335 and t.nature >= 3.0:
            t.nature = max(0.0, t.nature - 0.05)

        t.update_visual()