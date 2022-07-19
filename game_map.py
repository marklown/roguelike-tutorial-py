from __future__ import annotations
from optparse import Option
from typing import Iterable, Iterator, List, Optional, TYPE_CHECKING
import numpy as np # type: ignore
from tcod.console import Console

from entity import Actor, Item
import tile_types
import entity_factories

if TYPE_CHECKING:
  from engine import Engine
  from entity import Entity

class GameMap:
  def __init__(self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()):
    self.engine = engine
    self.width, self.height = width, height
    self.entities = set(entities)
    self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")
    self.visible = np.full((width, height), fill_value=False, order="F")
    self.expolored = np.full((width, height), fill_value=False, order="F")
    self.stairs_down_location = (0, 0)

  @property
  def game_map(self) -> GameMap:
    return self

  @property
  def actors(self) -> Iterator[Actor]:
    """Iterate over this maps living actors"""
    yield from (
      entity
      for entity in self.entities
      if isinstance(entity, Actor) and entity.is_alive
    )

  @property
  def items(self) -> Iterator[Item]:
    """Iterate over this maps items"""
    yield from (
      entity for entity in self.entities if isinstance(entity, Item)
    )

  def get_blocking_entity_at_location(self, x: int, y: int) -> Optional[Entity]:
    for entity in self.entities:
      if entity.blocks_movement and entity.x == x and entity.y == y:
        return entity

  def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
    for actor in self.actors:
      if actor.x == x and actor.y == y:
        return actor
    return None

  def get_closest_actor_in_range(self, range: int) -> Optional[Actor]:
    """Get the closest actor to the player"""
    closest: Actor = None
    closest_distance = range + 1.0
    # Find the closest actor to target
    for actor in self.actors:
      if actor is not self.engine.player and self.visible[actor.x, actor.y]:
        distance = self.engine.player.distance(actor.x, actor.y)
        if distance < closest_distance:
          closest = actor
          closest_distance = distance
    return closest

  def in_bounds(self, x: int, y: int) -> bool:
    return 0 <= x < self.width and 0 <= y < self.height

  def render(self, console: Console) -> None:
    console.tiles_rgb[0:self.width, 0:self.height] = np.select(
      condlist=[self.visible, self.expolored],
      choicelist=[self.tiles["light"], self.tiles["dark"]],
      default=tile_types.fog
    )

    entities_sorted_for_rendering = sorted(
      self.entities, key=lambda x: x.render_order.value
    )

    for entity in entities_sorted_for_rendering:
      # Only print entities that are in FOV
      if self.visible[entity.x, entity.y]:
        console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)


  @property
  def debug_spawnable(self) -> List[Entity]:
    return [
      entity_factories.orc,
      entity_factories.troll,
      entity_factories.health_potion,
      entity_factories.confusion_scroll,
      entity_factories.lightning_scroll,
      entity_factories.fireball_scroll,
      entity_factories.leather_armor,
      entity_factories.chain_mail,
      entity_factories.dagger,
      entity_factories.short_sword,
      entity_factories.green_apple,
      entity_factories.red_apple,
      entity_factories.bow,
    ]

  def debug_spawn_entity(self, entity: Entity, x: int, y: int) -> None:
    entity.spawn(game_map=self, x=x, y=y)  


class GameWorld:
  """Holds the settings for the GameMap and generates new maps for each floor descended"""
  def __init__(
    self,
    *,
    engine: Engine,
    map_width: int,
    map_height: int,
    max_rooms: int, 
    room_min_size: int,
    room_max_size: int,
    current_floor: int = 0
  ):
    self.engine = engine
    self.map_width = map_width
    self.map_height = map_height
    self.max_rooms = max_rooms
    self.room_min_size = room_min_size
    self.room_max_size = room_max_size
    self.current_floor = current_floor

  def generate_floor(self) -> None:
    from procgen import generate_dungeon
    self.current_floor += 1
    self.engine.game_map = generate_dungeon(
      max_rooms=self.max_rooms,
      room_min_size=self.room_min_size,
      room_max_size=self.room_max_size,
      map_width=self.map_width,
      map_height=self.map_height,
      engine=self.engine
    )
