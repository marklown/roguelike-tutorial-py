from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType
from input_handlers import (
  SingleRangedAttackHandler
) 
import actions
from exceptions import (
  Impossible
)
from entity import (
  Actor
)
import colors

if TYPE_CHECKING:
  from entity import Item


class Equippable(BaseComponent):
  parent: Item

  def __init__(
    self,
    equipment_type: EquipmentType,
    power_bonus: int = 0,
    defense_bonus: int = 0,
    durability: int = 0,
  ):
    self.equipment_type = equipment_type
    self.power_bonus = power_bonus
    self.defense_bonus = defense_bonus
    self.durability = durability


class RangedWeapon(Equippable):
  def __init__(
    self,
    range: int,
    power: int,
  ):
    self.range = range
    self.power = power
    super().__init__(
      equipment_type=EquipmentType.RANGED_WEAPON,
    )

  def get_action(self, firing_entity: Actor) -> Optional[SingleRangedAttackHandler]:
    self.engine.message_log.add_message("Select a target location", colors.needs_target)
    return SingleRangedAttackHandler(
      self.engine,
      callback=lambda xy: actions.ItemAction(firing_entity, self.parent, xy)
    )

  def activate(self, action: actions.ItemAction) -> None:
    firing_entity = action.entity
    target = action.target_actor

    if not self.engine.game_map.visible[action.target_xy]:
      raise Impossible("You cannot target an area that you cannot see.")
    if not target:
      raise Impossible("You must select an enemy to target.")
    if target is firing_entity:
      raise Impossible("You cannot fire weapons at yourself!")

    self.engine.message_log.add_message(
      f"You fire the {self.parent.name} and strike {target.name} for {self.power} damage"
    )
    target.fighter.take_damage(self.power)
