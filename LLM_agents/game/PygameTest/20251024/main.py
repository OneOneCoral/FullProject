# --- main.py ---
import pygame, time
from camera import Camera
from player import Player
from world import World
from profiler import Profiler
from config import *
from rendering import Rendering
from input_handler import InputHandler
from mini_map import MiniMap

print("hi")

pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
player = Player((MAP_WIDTH*TILE_SIZE//2, MAP_HEIGHT*TILE_SIZE//2))
cam = Camera()
render = Rendering()
world = World(MAP_WIDTH, MAP_HEIGHT)
minimap = MiniMap.create_mini_map(world)
profiler = Profiler()
input_handler = InputHandler()  # create an instance once, outside the loop
show_minimap = input_handler.is_stick_up()

# Initialize joystick
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() > 0 else None
if joystick:
    joystick.init()
    print(f"[INPUT] Controller connected: {joystick.get_name()}")
else:
    print("[INPUT] No joystick detected.")


# Prebuild minimap (rebuild every few seconds instead of per frame)





minimap_timer = 0.0


running = True
while running:




    profiler.start('frame')
    dt = clock.tick(FPS)


    # --- Events ---
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEWHEEL:
            cam.target_zoom *= 1.0 + e.y * 0.1

    keys = pygame.key.get_pressed()


    # --- Update ---

    profiler.start('player_update')

    # --- Controller input ---
    player_input_for_movement = input_handler.get_movement()
    action = input_handler.handle_world_action(world, player.rect)
    input_handler.update_buttons()  # refresh current button states
    input_handler.show_pressed_buttons()  # optional: print pressed buttons
    # Then update the player:
    player.update(dt, player_input_for_movement, action, world)

    profiler.stop('player_update')




    profiler.start('world_update')
    world.simulate_step(UPDATE_STEP_LIMIT)
    profiler.stop('world_update')



    profiler.start('camera_update')
    cam.update(player.rect)
    profiler.stop('camera_update')


    # --- Draw ---
    window.fill((10, 10, 30))
    profiler.start('render')
    render.draw_non_player(window, cam, world)
    player.draw(window, cam)
    profiler.stop('render')


    pygame.display.flip()
    profiler.stop('frame')




    if pygame.time.get_ticks() % 3000 < 16:
        profiler.report()


pygame.quit()