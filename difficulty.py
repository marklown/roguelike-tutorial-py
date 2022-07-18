from __future__ import annotations
from typing import Dict, List, Tuple, TYPE_CHECKING
import random

import entity_factories

if TYPE_CHECKING:
  from entity import Entity

"""
Lists of Tuples representing increasing difficulty by floor.
First number is the floor, second number is the value.
"""

max_items_by_floor = [
  (1, 1),
  (4, 2),
]

max_monsters_by_floor = [
  (1, 2),
  (4, 3),
  (6, 5),
]

"""
Control the chances of items and enemies appearing on each floor
"""

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
  0: [(entity_factories.health_potion, 10)],
  2: [(entity_factories.confusion_scroll, 10), (entity_factories.dagger, 5), (entity_factories.leather_armor, 10)],
  4: [(entity_factories.lightning_scroll, 20), (entity_factories.short_sword, 5)],
  6: [(entity_factories.fireball_scroll, 20), (entity_factories.chain_mail, 10)],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],
    3: [(entity_factories.troll, 15)],
    5: [(entity_factories.troll, 30)],
    7: [(entity_factories.troll, 60)],
}

def get_max_value_by_floor(
  max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
  for floor_minimum, value in max_value_by_floor:
    if floor_minimum > floor:
      break;
    else:
      current_value = value
  return current_value

def get_random_entities_by_floor(
  weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
  number_of_entities: int,
  floor: int,
) -> List[Entity]:
  entity_weighted_chances = {}
  for key, values in weighted_chances_by_floor.items():
    if key > floor:
      break
    else:
      for value in values:
        entity = value[0]
        weighted_chance = value[1]
        entity_weighted_chances[entity] = weighted_chance

  entities = list(entity_weighted_chances.keys())
  entity_weighted_chance_values = list(entity_weighted_chances.values())

  chosen_entities = random.choices(
      entities, weights=entity_weighted_chance_values, k=number_of_entities
  )

  return chosen_entities