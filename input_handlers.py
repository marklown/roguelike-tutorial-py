from __future__ import annotations
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union
from xml.dom.minidom import Entity
from numpy import isin
import os
import tcod
from actions import (
  Action, 
  BumpAction, 
  PickupAction,
  DropItemAction,
  WaitAction,
)
import colors
import exceptions

if TYPE_CHECKING:
  from engine import Engine
  from entity import Item

MOVE_KEYS = {
  # Arrows
  tcod.event.K_UP: (0, -1),
  tcod.event.K_DOWN: (0, 1),
  tcod.event.K_LEFT: (-1, 0),
  tcod.event.K_RIGHT: (1, 0),
  #tcod.event.K_HOME: (-1, -1),
  #tcod.event.K_END: (-1, 1),
  #tcod.event.K_PAGEUP: (1, -1),
  #tcod.event.K_PAGEDOWN: (1, 1),
  # Numpad
  tcod.event.K_KP_2: (0, 1),
  tcod.event.K_KP_4: (-1, 0),
  tcod.event.K_KP_6: (1, 0),
  tcod.event.K_KP_8: (0, -1),
  #tcod.event.K_KP_1: (-1, 1),
  #tcod.event.K_KP_3: (1, 1),
  #tcod.event.K_KP_7: (-1, -1),
  #tcod.event.K_KP_9: (1, -1),
  # VI
  tcod.event.K_h: (-1, 0),
  tcod.event.K_j: (0, 1),
  tcod.event.K_k: (0, -1),
  tcod.event.K_l: (1, 0),
  #tcod.event.K_y: (-1, -1),
  #tcod.event.K_u: (1, -1),
  #tcod.event.K_b: (-1, 1),
  #tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
  tcod.event.K_PERIOD,
  tcod.event.K_KP_5,
  tcod.event.K_CLEAR,
}

"""
An event handler return value which can trigger an action or switch active handlers.
If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then MainGameEventHandler
will become the active handler.
"""
ActionOrHandler = Union[Action, "BaseEventHandler"]

class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
  def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
    """Handle an event and return the next active event handler"""
    state = self.dispatch(event)
    if isinstance(state, BaseEventHandler):
      return state
    assert not isinstance(state, Action), f"{self!r} can not handle actions."
    return self

  def on_render(self, console: tcod.Console) -> None:
    raise NotImplementedError()

  def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
    raise SystemExit()

"""
Event handler class
"""
class EventHandler(BaseEventHandler):
  def __init__(self, engine: Engine):
    self.engine = engine

  def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
    """Handle events for input handlers with an engine"""
    action_or_state = self.dispatch(event)
    if isinstance(action_or_state, BaseEventHandler):
      return action_or_state
    if self.handle_action(action_or_state):
      # A valid action was performed
      if not self.engine.player.is_alive:
        # The player was killed some time during or after the action
        return GameOverEventHandler(self.engine)
      return MainGameEventHandler(self.engine)
    return self

  def handle_action(self, action: Optional[Action]) -> bool:
    """Handle actions returned from event methods"""
    """Returns true if the action will advance a turn"""
    if action is None:
      return False

    try:
      action.perform()
    except exceptions.Impossible as exc:
      self.engine.message_log.add_message(exc.args[0], colors.impossible)
      return False

    self.engine.handle_enemy_turns()
    self.engine.update_fov()
    return True

  def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
    if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
      self.engine.mouse_location = event.tile.x, event.tile.y

  def on_render(self, console: tcod.Console) -> None:
    self.engine.render(console)


"""
Handle events during gameplay
"""
class MainGameEventHandler(EventHandler):
  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
    action: Optional[Action] = None

    key = event.sym
    player = self.engine.player

    if key in MOVE_KEYS:
      dx, dy = MOVE_KEYS[key]
      action = BumpAction(player, dx, dy)
    elif key in WAIT_KEYS:
      action = WaitAction(player)
    elif key == tcod.event.K_ESCAPE:
      raise SystemExit()
    elif key == tcod.event.K_v:
      return HistoryViewer(self.engine)
    elif key == tcod.event.K_g:
      action = PickupAction(player)
    elif key == tcod.event.K_i:
      return InventoryActivateHandler(self.engine)
    elif key == tcod.event.K_d:
      return InventoryDropHandler(self.engine)
    elif key == tcod.event.K_SLASH:
      return LookHandler(self.engine)
    elif key == tcod.event.K_BACKSLASH:
      return DebugSpawnEntityEventHandler(self.engine)

    return action


"""
Handle events after the player is dead
"""
class GameOverEventHandler(EventHandler):
  def on_quit(self) -> None:
    """Handle exiting out of a finished game"""
    if os.path.exists("savegame.sav"):
      os.remove("savegame.sav") # Delete the active save
    raise exceptions.QuitWithoutSaving()

  def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
    self.on_quit()

  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
    if event.sym == tcod.event.K_ESCAPE:
      self.on_quit()


CURSOR_Y_KEYS = {
  tcod.event.K_UP: -1,
  tcod.event.K_DOWN: 1,
  tcod.event.K_PAGEUP: -10,
  tcod.event.K_PAGEDOWN: 10,
  tcod.event.K_j: -1,
  tcod.event.K_k: 1
}

"""
Super class to handle user input for actions which require special input. 
"""
class AskUserEventHandler(EventHandler):
  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
    # By default any key exits the input handler
    if event.sym in { # ignore modifier keys
      tcod.event.K_LSHIFT,
      tcod.event.K_RSHIFT,
      tcod.event.K_LCTRL,
      tcod.event.K_RCTRL,
      tcod.event.K_LALT,
      tcod.event.K_RALT,
    }:
      return None
    return self.on_exit()

  def ev_mousebuttondown(
    self, 
    event: tcod.event.MouseButtonDown
  ) -> Optional[ActionOrHandler]:
    # By default any mouse click exits the input handler
    return self.on_exit()

  def on_exit(self) -> Optional[ActionOrHandler]:
    # Called when the user is trying to exit or cancel the action
    return MainGameEventHandler(self.engine)

"""
Handle user selection of inventory items
"""
class InventoryEventHandler(AskUserEventHandler):
  TITLE = "<missing title>"

  def on_render(self, console: tcod.Console) -> None:
    super().on_render(console)
    number_of_items = len(self.engine.player.inventory.items)
    height = number_of_items + 2
    if height <= 3:
      height = 3
    width = len(self.TITLE) + 4

    # position the menu so it does not cover the player
    if self.engine.player.x <= 30:
      x = 40
    else:
      x = 0
    y= 0

    console.draw_frame(
      x=x,
      y=y,
      width=width,
      height=height,
      title=self.TITLE,
      clear=True,
      fg=(255,255,255),
      bg=(0,0,0),
    )

    if number_of_items > 0:
      for i, item in enumerate(self.engine.player.inventory.items):
        item_key = chr(ord("a") + i)
        console.print(x+1,y+i+1,f"({item_key}) {item.name}")
    else:
      console.print(x+1,y+1, "(Empty)")

  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
    player = self.engine.player
    key = event.sym
    index = key - tcod.event.K_a
    if 0 <= index <= 26:
      try:
        selected_item = player.inventory.items[index]
      except IndexError:
        self.engine.message_log.add_message("Invalid choice", colors.invalid)
        return None
      return self.on_item_selected(selected_item)
    return super().ev_keydown(event)

  def on_item_selected(self, item: Item) -> Optional[Action]:
    raise NotImplementedError()

"""
Handles using an inventory item
"""
class InventoryActivateHandler(InventoryEventHandler):
  TITLE = "Select an item to use"

  def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
    return item.consumable.get_action(self.engine.player)

"""
Handles dropping an inventory item
"""
class InventoryDropHandler(InventoryEventHandler):
  TITLE = "Select an item to drop"

  def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
    return DropItemAction(self.engine.player, item)

CONFIRM_KEYS = {
  tcod.event.K_RETURN,
  tcod.event.K_KP_ENTER,
}

"""
Handles asking the user for an index on the map
"""
class SelectIndexHandler(AskUserEventHandler):
  def __init__(self, engine: Engine):
    super().__init__(engine)
    player = self.engine.player
    engine.mouse_location = player.x, player.y

  def on_render(self, console: tcod.Console) -> None:
    super().on_render(console)
    x, y = self.engine.mouse_location
    console.tiles_rgb["bg"][x,y] = colors.white
    console.tiles_rgb["fg"][x,y] = colors.black

  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
    key = event.sym
    if key in MOVE_KEYS:
      modifier = 1 # Holding modifier keys will speed movement
      if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
        modifier *= 5
      if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
        modifier *= 10
      if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
        modifier *= 20

      x, y = self.engine.mouse_location
      dx, dy = MOVE_KEYS[key]
      x += dx * modifier
      y += dy * modifier

      # clamp the cursor index to the map size
      x = max(0, min(x, self.engine.game_map.width -1))
      y = max(0, min(y, self.engine.game_map.height - 1))
      self.engine.mouse_location = x, y
      return None
    elif key in CONFIRM_KEYS:
      return self.on_index_selected(*self.engine.mouse_location)
    
    return super().ev_keydown(event)

  def ev_mousebuttondown(
    self, 
    event: tcod.event.MouseButtonDown
  ) -> Optional[ActionOrHandler]:
    if self.engine.game_map.in_bounds(*event.tile):
      if event.button == 1:
        return self.on_index_selected(*event.tile)
    return super().ev_mousebuttondown(event)

  def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
    raise NotImplementedError()

"""
Let the player look around the map using keyboard
"""
class LookHandler(SelectIndexHandler):
  def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
    return MainGameEventHandler(self.engine)


"""
Handles targeting a single enemy. Only the selected enemy is affected.
"""
class SingleRangedAttackHandler(SelectIndexHandler):
  def __init__(self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]):
    super().__init__(engine)
    self.callback = callback

  def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
    return self.callback((x, y))


"""
Handles targeting an area for area attach effects.
"""
class AreaRangedAttackHandler(SelectIndexHandler):
  def __init__(
    self, 
    engine: Engine,
    radius: int,
    callback: Callable[[Tuple[int, int]], Optional[Action]],
  ):
    super().__init__(engine)
    self.radius = radius
    self.callback = callback

  def on_render(self, console: tcod.Console) -> None:
    super().on_render(console) # Highlight the tile under the cursor
    x, y = self.engine.mouse_location
    # Draw a rectangle around the area
    console.draw_frame(
      x=x-self.radius-1,
      y=y-self.radius-1,
      width=self.radius**2,
      height=self.radius**2,
      fg=colors.red,
      clear=False
    )

  def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
    return self.callback((x, y))

class PopupMessage(BaseEventHandler):
  """Display a popup text window."""

  def __init__(self, parent_handler: BaseEventHandler, text: str):
    self.parent = parent_handler
    self.text = text

  def on_render(self, console: tcod.Console) -> None:
    """Render the parent and dim the result, then print the message on top."""
    self.parent.on_render(console)
    console.tiles_rgb["fg"] //= 8
    console.tiles_rgb["bg"] //= 8

    console.print(
      console.width // 2,
      console.height // 2,
      self.text,
      fg=colors.white,
      bg=colors.black,
      alignment=tcod.CENTER,
    )

  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
      """Any key returns to the parent handler."""
      return self.parent


"""
Print the history on a larger window which can be navigated.
"""
class HistoryViewer(EventHandler):

  def __init__(self, engine: Engine):
    super().__init__(engine)
    self.log_length = len(engine.message_log.messages)
    self.cursor = self.log_length - 1

  def on_render(self, console: tcod.Console) -> None:
    super().on_render(console)  # Draw the main state as the background.

    log_console = tcod.Console(console.width - 6, console.height - 6)

    # Draw a frame with a custom banner title.
    log_console.draw_frame(0, 0, log_console.width, log_console.height)
    log_console.print_box(
      0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
    )

    # Render the message log using the cursor parameter.
    self.engine.message_log.render_messages(
      log_console,
      1,
      1,
      log_console.width - 2,
      log_console.height - 2,
      self.engine.message_log.messages[: self.cursor + 1],
    )
    log_console.blit(console, 3, 3)

  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
    # Fancy conditional movement to make it feel right.
    if event.sym in CURSOR_Y_KEYS:
      adjust = CURSOR_Y_KEYS[event.sym]
      if adjust < 0 and self.cursor == 0:
        # Only move from the top to the bottom when you're on the edge.
        self.cursor = self.log_length - 1
      elif adjust > 0 and self.cursor == self.log_length - 1:
        # Same with bottom to top movement.
        self.cursor = 0
      else:
        # Otherwise move while staying clamped to the bounds of the history log.
        self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
    elif event.sym == tcod.event.K_HOME:
      self.cursor = 0  # Move directly to the top message.
    elif event.sym == tcod.event.K_END:
      self.cursor = self.log_length - 1  # Move directly to the last message.
    else:  # Any other key moves back to the main game state.
      return MainGameEventHandler(self.engine)
    return None


"""
DEBUG spawn any entity event handler
A better way might be to create a scroll that allows the player to spawn anything?
"""
class DebugSpawnEntityEventHandler(AskUserEventHandler):
  TITLE = "DEBUG Spawn Any Entity"

  def on_render(self, console: tcod.Console) -> None:
    super().on_render(console)
    number_of_items = len(self.engine.game_map.debug_spawnable)
    height = number_of_items + 2
    if height <= 3:
      height = 3
    width = len(self.TITLE) + 8

    # position the menu so it does not cover the player
    if self.engine.player.x <= 30:
      x = 40
    else:
      x = 0
    y= 0

    console.draw_frame(
      x=x,
      y=y,
      width=width,
      height=height,
      title=self.TITLE,
      clear=True,
      fg=(255,255,255),
      bg=(0,0,0),
    )

    if number_of_items > 0:
      for i, entity in enumerate(self.engine.game_map.debug_spawnable):
        entity_key = chr(ord("a") + i)
        console.print(x+1,y+i+1,f"{entity_key} {entity.name}")
    else:
      console.print(x+1,y+1, "(Empty)")

  def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
    player = self.engine.player
    key = event.sym
    index = key - tcod.event.K_a
    if 0 <= index <= 26:
      try:
        selected_entity = self.engine.game_map.debug_spawnable[index]
      except IndexError:
        self.engine.message_log.add_message("Invalid choice", colors.invalid)
        return None

      x,y = player.x, player.y
      self.engine.game_map.debug_spawn_entity(entity=selected_entity, x=player.x, y=player.y+1) 
      self.engine.message_log.add_message(
        f"DEBUG spawned a {selected_entity.name}"
      )
    return super().ev_keydown(event)