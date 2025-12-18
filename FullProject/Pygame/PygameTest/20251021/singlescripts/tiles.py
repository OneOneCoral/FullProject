import pygame

from config import TILE_SIZE, TREE_THRESHOLD

class Tile:
    """Represents a single terrain tile with water, earth, nature, and heat characteristics."""

    __slots__ = ("x", "y", "rect", "water", "earth", "nature", "heat", "color", "is_obstacle")

    def __init__(self, x, y, height, temp):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

        # base values
        self.water = max(0.0, min(1.0, 1.0 - (height + 0.25) * 1.2)) if height < 0.5 else 0.0
        self.earth = max(0.0, min(1.0, 1.0 - self.water))
        self.nature = 0.0
        self.heat = float(temp)
        self.is_obstacle = False
        self.update_visual()

    # -----------------------------
    # == Core Helpers
    # -----------------------------
    def fertile(self):
        return (0.22 <= self.water <= 0.65) and (285 <= self.heat <= 315) and (self.earth > 0.3)

    def harsh(self):
        return (self.water < 0.12) or (self.heat >= 330) or (self.earth < 0.2)

    # -----------------------------
    # == Tile Interaction
    # -----------------------------
    def grow(self, amount=1.0):
        """Increase vegetation (simulate planting)."""
        self.nature = min(5.0, self.nature + amount)
        self.update_visual()

    def burn(self, amount=1.0):
        """Decrease vegetation and heat the tile (simulate burning)."""
        self.nature = max(0.0, self.nature - amount)
        self.heat += 10.0 * amount
        self.update_visual()

    # -----------------------------
    # == Visual Representation
    # -----------------------------
    def update_visual(self):
        """Choose color based on water, earth, nature, and heat levels."""
        self.is_obstacle = self.nature >= TREE_THRESHOLD

        # Water dominant
        if self.water > 0.68:
            self.color = (0, 0, 160)  # deep water
        elif self.water > 0.38:
            self.color = (20, 100, 200)  # shallow water
        else:
            # Vegetation spectrum
            if self.nature >= 4.5:
                self.color = (0, 70, 0)      # dense forest
            elif self.nature >= 3.5:
                self.color = (10, 115, 10)   # bush
            elif self.nature >= 2.0:
                self.color = (60, 170, 60)   # tall grass
            elif self.nature >= 1.0:
                self.color = (105, 200, 105) # grass
            else:
                # Bare ground reacts to heat
                base = int(170 + (self.heat - 300) * 0.35)
                base = max(80, min(230, base))
                self.color = (base, base - 20, 80)
