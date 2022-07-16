from logging import root
from numpy import place
import tcod
import copy
from engine import Engine
from procgen import generate_dungeon
import entity_factories
import colors
import traceback
import exceptions
import input_handlers

def main() -> None:
  screen_width = 80
  screen_height = 50
  map_width = 80
  map_height = 43
  room_max_size = 10
  room_min_size = 6
  max_rooms = 30
  max_monsters_per_room = 2
  max_items_per_room = 2

  tileset = tcod.tileset.load_tilesheet("fonts/terminal16x16_gs_ro.png", 16, 16, tcod.tileset.CHARMAP_CP437)

  player = copy.deepcopy(entity_factories.player);
  engine = Engine(player=player)
  engine.game_map = generate_dungeon(
    max_rooms=max_rooms,
    room_min_size=room_min_size,
    room_max_size=room_max_size,
    map_width=map_width,
    map_height=map_height,
    max_monsters_per_room=max_monsters_per_room,
    max_items_per_room=max_items_per_room,
    engine=engine
  ) 
  engine.update_fov()

  engine.message_log.add_message(
    "Hello and welcome, adventurer, to the dungeons of doom!",
    colors.welcome_text
  )

  handler: input_handlers.BaseEventHandler = input_handlers.MainGameEventHandler(engine)

  with tcod.context.new_terminal(screen_width, screen_height, tileset=tileset, title="rogue", vsync=True) as context:
    root_console = tcod.Console(screen_width, screen_height, order="F")
    try:
      while True:
        root_console.clear()
        handler.on_render(console=root_console)
        context.present(root_console)

        try:
          for event in tcod.event.wait():
            context.convert_event(event)
            handler = handler.handle_events(event)
        except Exception:
          traceback.print_exc()
          if isinstance(handler, input_handlers.EventHandler):
            handler.engine.message_log.add_message(
              traceback.format_exc(), colors.error
            )
    except exceptions.QuitWithoutSaving:
      """Quit without saving"""
      raise
    except SystemExit:
      """Save and quit"""
      raise
    except BaseException:
      """Save on any other unexpected exception"""
      raise


if __name__ == "__main__":
  main()