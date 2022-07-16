from __future__ import annotations
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
    ]

  def debug_spawn_entity(self, entity: Entity, x: int, y: int) -> None:
    entity.spawn(game_map=self, x=x, y=y)  