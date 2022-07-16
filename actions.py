from __future__ import annotations
from typing import Optional, Tuple, TYPE_CHECKING

import colors
import exceptions

if TYPE_CHECKING:
  from engine import Engine
  from entity import Actor, Entity, Item

"""
Base action class
"""
class Action:
  def __init__(self, entity: Actor) -> None:
    super().__init__()
    self.entity = entity

  @property
  def engine(self) -> Engine:
    return self.entity.game_map.engine

  def perform(self) -> None:
    raise NotImplementedError()

"""
Base Action with a given direction (x, y)
"""
class ActionWithDirection(Action):
  def __init__(self, entity: Actor, dx: int, dy: int):
    super().__init__(entity)
    self.dx = dx
    self.dy = dy

  @property
  def dest_xy(self) -> Tuple[int, int]:
    return self.entity.x + self.dx, self.entity.y + self.dy

  @property
  def blocking_entity(self) -> Optional[Entity]:
    return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

  @property
  def target_actor(self) -> Optional[Actor]:
    """Return the actor at this actions destination"""
    return self.engine.game_map.get_actor_at_location(*self.dest_xy)

  def perform(self) -> None:
    raise NotImplementedError()

"""
Melee attack action
"""
class MeleeAction(ActionWithDirection):
  def perform(self) -> None:
    target = self.target_actor
    if not target:
      raise exceptions.Impossible("Nothing to attack")

    damage = self.entity.fighter.power - target.fighter.defense

    attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
    if self.entity is self.engine.player:
      attack_color = colors.player_atk
    else:
      attack_color = colors.enemy_atk

    if damage > 0:
      self.engine.message_log.add_message(f"{attack_desc} for {damage} hit points", attack_color)
      target.fighter.hp -= damage
    else:
      self.engine.message_log.add_message(f"{attack_desc} but does no damage", attack_color)

"""
Movement action
"""
class MovementAction(ActionWithDirection):
  def perform(self) -> None:
    dest_x, dest_y = self.dest_xy

    if not self.engine.game_map.in_bounds(dest_x, dest_y):
      raise exceptions.Impossible("The way is blocked")
    if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
      raise exceptions.Impossible("The way is blocked")
    if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
      raise exceptions.Impossible("The way is blocked")

    self.entity.move(self.dx, self.dy)

"""
Resolves to either melee attack or move action
"""
class BumpAction(ActionWithDirection):
  def perform(self) -> None:
    if self.target_actor:
      return MeleeAction(self.entity, self.dx, self.dy).perform()
    else:
      return MovementAction(self.entity, self.dx, self.dy).perform()

"""
No Action, just stay put
"""
class WaitAction(Action):
  def perform(self) -> None:
    pass

"""
Action taken by an item
"""
class ItemAction(Action):
  def __init__(
    self,
    entity: Actor, # The entity using/invoking this item (not necessarily the target)
    item: Item,
    target_xy: Optional[Tuple[int, int]] = None,
  ):
    super().__init__(entity)
    self.item = item
    if not target_xy:
      # If target not set, the parent entity is the target
      target_xy = entity.x, entity.y
    self.target_xy = target_xy

  @property
  def target_actor(self) -> Optional[Actor]:
    """Get the actor this action is targeting"""
    return self.engine.game_map.get_actor_at_location(*self.target_xy)

  def perform(self) -> None:
    """Invoke the items ability"""
    self.item.consumable.activate(self)

"""
Action to pick up an Item from the map
"""
class PickupAction(Action):
  def __init__(self, entity: Actor):
    super().__init__(entity)

  def perform(self) -> None:
    actor_x = self.entity.x
    actor_y = self.entity.y
    inventory = self.entity.inventory

    for item in self.engine.game_map.items:
      if actor_x == item.x and actor_y == item.y:
        if len(inventory.items) >= inventory.capacity:
          raise exceptions.Impossible("You cannot pick up this item, your inventory is full")

        self.engine.game_map.entities.remove(item)
        item.parent = self.entity.inventory
        inventory.items.append(item)
        self.engine.message_log.add_message(f"You pick up the {item.name}")
        return

    raise exceptions.Impossible("There is nothing to pick up here")

"""
Action to drop an item from inventory
"""
class DropItemAction(ItemAction):
  def perform(self) -> None:
    self.entity.inventory.drop(self.item)