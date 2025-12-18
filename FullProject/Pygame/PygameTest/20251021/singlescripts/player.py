# -------------------- player.py --------------------
import pygame
import math
from config import TILE_SIZE


class Player:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], TILE_SIZE, TILE_SIZE)
        self.color = (220, 60, 60)

        # movement physics
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = 700.0      # how fast player accelerates (px/s²)
        self.max_speed = 240.0         # max speed (px/s)
        self.ground_drag = 0.85        # 0..1 fraction of velocity kept per frame
        self.status_drag = 1.0         # multiplier for in-game effects (mud, water, fatigue)

    def apply_physics(self, move_dir, dt):
        """Acceleration, drag and speed clamping."""
        # accelerate toward input direction
        if move_dir.length_squared() > 0:
            accel_vec = move_dir * self.acceleration * dt
            self.velocity += accel_vec

        # apply drag
        self.velocity *= (self.ground_drag * self.status_drag)

        # limit speed
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

    def update(self, dt_ms, move_dir, action, cam):
        dt = dt_ms / 1000.0
        self.apply_physics(move_dir, dt)

        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt

    def draw(self, surf, cam):
        pygame.draw.rect(surf, self.color, cam.apply(self.rect))

