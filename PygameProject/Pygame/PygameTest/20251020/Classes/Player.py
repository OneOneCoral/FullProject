import pygame
# ==========================================================
# == PLAYER
# ==========================================================
class Player:
    def __init__(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], 16, 16)
        self.color = (0, 255, 0)
        self.speed = 200

    def handle_input(self, keys, joystick):
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]: move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x += 1

        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            if abs(axis_x) > 0.2 or abs(axis_y) > 0.2:
                move.x = axis_x
                move.y = axis_y
            print(f"[Joystick Debug] Axis X: {axis_x:.2f}, Axis Y: {axis_y:.2f}")
        if move.length_squared() > 0:
            move = move.normalize()
        return move

    def update(self, dt, move):
        vel = move * self.speed * dt / 1000.0
        self.rect.x += vel.x
        self.rect.y += vel.y

    def draw(self, surf, cam):
        r = cam.apply(self.rect)
        pygame.draw.rect(surf, self.color, r)