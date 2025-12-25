import pygame
from config import TILE_SIZE
from mini_map import MiniMap


class InputHandler:
    def __init__(self):
        pygame.joystick.init()
        self.joystick = None
        self.buttons = {}  # store current button states

        # Try to connect to first controller
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"[INPUT] Controller connected: {self.joystick.get_name()}")
        else:
            print("[INPUT] No controller detected – using neutral input.")

    def get_movement(self):
        move = pygame.Vector2(0, 0)
        axis_x = 0
        axis_y = 0

        if self.joystick:
            axis_x = self.joystick.get_axis(0)
            axis_y = self.joystick.get_axis(1)
        else:
            # Debug message if no controller is connected
            print("[INPUT WARNING] No joystick detected — please connect a controller for movement input.")
            return move  # Early exit, prevents unnecessary processing

        # Apply deadzone threshold
        if abs(axis_x) > 0.2 or abs(axis_y) > 0.2:
            move.x = axis_x
            move.y = axis_y

        # Normalize vector if movement exists
        if move.length_squared() > 0:
            move = move.normalize()

        return move



    def show_pressed_buttons(self):
        """Print currently pressed buttons (or display them in HUD)."""
        pressed = [name for name, val in self.buttons.items() if val]
        if pressed:
            print(f"[INPUT] Buttons pressed: {', '.join(pressed)}")
    # ------------------------------------------------------------
    # MENU / BUTTON STATE HANDLING
    # ------------------------------------------------------------
    def update_buttons(self):
        """Store all current button states (for menus or debugging)."""
        if not self.joystick:
            self.buttons = {}
            return

        self.buttons = {
            "A": self.joystick.get_button(0),
            "B": self.joystick.get_button(1),
            "X": self.joystick.get_button(2),
            "Y": self.joystick.get_button(3),
            "LB": self.joystick.get_button(4),
            "RB": self.joystick.get_button(5),
            "BACK": self.joystick.get_button(6),
            "START": self.joystick.get_button(7),
        }

    # ------------------------------------------------------------
    # OPTIONAL CONTROLLER CHECK
    # ------------------------------------------------------------
    def check_controller(self):
        """Reconnect controller if unplugged."""
        if self.joystick and not self.joystick.get_init():
            print("[INPUT] Controller disconnected.")
            self.joystick = None
        elif not self.joystick and pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"[INPUT] Controller reconnected: {self.joystick.get_name()}")

    def handle_world_action(self, world, player_rect):
        if not self.joystick:
            return

        px, py = int(player_rect.centerx // TILE_SIZE), int(player_rect.centery // TILE_SIZE)
        if not (0 <= px < world.w and 0 <= py < world.h):
            return

        tile = world.tiles[py][px]
        a_pressed = self.joystick.get_button(0)
        b_pressed = self.joystick.get_button(1)

        if a_pressed:
            tile.nature = min(5.0, tile.nature + 0.25)
            tile.update_visual()
        elif b_pressed:
            tile.nature = max(0.0, tile.nature - 0.25)
            tile.update_visual()

    def is_stick_up(self):
        if not self.joystick:
            return False
        if self.joystick.get_axis(1) < -0.8:
            MiniMap.create_mini_map()
            MiniMap.draw()

