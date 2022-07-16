from __future__ import annotations
from typing import Optional, TYPE_CHECKING

import actions
import colors
from components.base_component import BaseComponent
from components.inventory import Inventory
from components.ai import (
  ConfusedEnemy
)
from input_handlers import (
  ActionOrHandler,
  SingleRangedAttackHandler,
  AreaRangedAttackHandler
)
from exceptions import Impossible

if TYPE_CHECKING:
  from entity import Actor, Item


class Consumable(BaseComponent):
  parent: Item

  def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
    return actions.ItemAction(consumer, self.parent)

  def activate(self, action: actions.ItemAction) -> None:
    raise NotImplementedError()

  def consume(self) -> None:
    entity = self.parent        # parent is an Item
    inventory = entity.parent   # items parent is the Inventory (or should be)
    if isinstance(inventory, Inventory):
      inventory.items.remove(entity) # remove the item from the inventory


class HealingConsumable(Consumable):
  def __init__(self, amount: int):
    super().__init__()
    self.amount = amount

  def activate(self, action: actions.ItemAction) -> None:
    consumer = action.entity
    amount_recovered = consumer.fighter.heal(self.amount)
    if amount_recovered > 0:
      self.engine.message_log.add_message(
        f"You consume the {self.parent.name}, and recover {amount_recovered} HP",
        colors.health_recovered
      )
      self.consume() # Remove the item from the inventory
    else:
      raise Impossible(f"You are already of perfect health")

class LightningDamageConsumable(Consumable):
  def __init__(self, damage: int, max_range: int) -> None:
    self.damage = damage
    self.max_range = max_range

  def activate(self, action: actions.ItemAction) -> None:
    consumer = action.entity
    target = None
    closest_distance = self.max_range + 1.0
    # Find the closest actor to target
    for actor in self.engine.game_map.actors:
      if actor is not consumer and self.parent.game_map.visible[actor.x, actor.y]:
        distance = consumer.distance(actor.x, actor.y)
        if distance < closest_distance:
          target = actor
          closest_distance = distance

    if target:
      self.engine.message_log.add_message(
        f"A bolt of lightning strikes the {target.name} with a loud bang, for {self.damage} damage!"
      )
      target.fighter.take_damage(self.damage)
      self.consume()
    else:
      raise Impossible("No enemy is close enough to strike")


class ConfusionConsumable(Consumable):
  def __init__(self, number_of_turns: int) -> None:
    self.number_of_turns = number_of_turns

  def get_action(self, consumer: Actor) -> Optional[SingleRangedAttackHandler]:
    self.engine.message_log.add_message("Select a target location", colors.needs_target)
    return SingleRangedAttackHandler(
      self.engine,
      callback=lambda xy: actions.ItemAction(consumer, self.parent, xy)
    )

  def activate(self, action: actions.ItemAction) -> None:
    consumer = action.entity
    target = action.target_actor

    if not self.engine.game_map.visible[action.target_xy]:
      raise Impossible("You cannot target an area that you cannot see")
    if not target:
      raise Impossible("You must select an enemy to target")
    if target is consumer:
      raise Impossible("You cannot confuse yourself")

    self.engine.message_log.add_message(
      f"The eyes of the {target.name} look vacant, as it starts to stumble around aimlessly",
      colors.status_effect_applied
    )
    target.ai = ConfusedEnemy(entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns)
    self.consume()


class FireballDamageConsumable(Consumable):
  def __init__(self, damage: int, radius: int) -> None:
    self.damage = damage
    self.radius = radius

  def get_action(self, consumer: Actor) -> Optional[AreaRangedAttackHandler]:
    self.engine.message_log.add_message("Select a target location", colors.needs_target)
    return AreaRangedAttackHandler(
      self.engine,
      radius=self.radius,
      callback=lambda xy: actions.ItemAction(consumer, self.parent, xy)
    )

  def activate(self, action: actions.ItemAction) -> None:
    target_xy = action.target_xy
    if not self.engine.game_map.visible[target_xy]:
      raise Impossible("You cannot target an area that you cannot see")

    targets_hit = False
    for actor in self.engine.game_map.actors:
      if actor.distance(*target_xy) <= self.radius:
        self.engine.message_log.add_message(
          f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage"
        )
        actor.fighter.take_damage(self.damage)
        targets_hit = True

    if not targets_hit:
      raise Impossible("There are no targets within the targeted area")

    self.consume()