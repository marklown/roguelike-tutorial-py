from components.ai import HostileEnemy
from components import (
  consumable,
  equippable
)
from components.fighter import Fighter
from components.inventory import Inventory
from components.equipment import Equipment
from entity import Actor, Item
import equipment_types

player = Actor(
  char="@", 
  color=(255, 255, 255), 
  name="Player", 
  ai_cls=HostileEnemy, # Doesn't actually use the AI, but ai_cls is required for all actors
  equipment=Equipment(),
  fighter=Fighter(hp=30, base_defense=2, base_power=4),
  inventory=Inventory(capacity=26)
)

orc = Actor(
  char="o", 
  color=(63, 127, 63), 
  name="Orc", 
  ai_cls=HostileEnemy,
  equipment=Equipment(),
  fighter=Fighter(hp=10, base_defense=0, base_power=4),
  inventory=Inventory(capacity=0)
)

troll = Actor(
  char="T", 
  color=(0, 127, 0), 
  name="Troll", 
  ai_cls=HostileEnemy,
  equipment=Equipment(),
  fighter=Fighter(hp=16, base_defense=2, base_power=6),
  inventory=Inventory(capacity=0)
)



health_potion = Item(
  char="!",
  color=(127, 0, 255),
  name="Potion of Healing",
  consumable=consumable.HealingConsumable(amount=4)
)

green_apple = Item(
  char=",",
  color=(32, 255, 32),
  name="Green apple",
  consumable=consumable.HealingConsumable(amount=2)
)

red_apple = Item(
  char=",",
  color=(255, 32, 32),
  name="Red apple",
  consumable=consumable.HealingConsumable(amount=3)
)

lightning_scroll = Item(
  char="~",
  color=(255, 255, 0),
  name="Scroll of Lightning",
  consumable=consumable.LightningDamageConsumable(damage=20, max_range=5)
)

confusion_scroll = Item(
  char="~",
  color=(207, 63, 255),
  name="Scroll of Confusion",
  consumable=consumable.ConfusionConsumable(number_of_turns=10)
)

fireball_scroll = Item(
  char="~",
  color=(255, 0, 0),
  name="Scroll of Conflagration",
  consumable=consumable.FireballDamageConsumable(damage=12, radius=3)
)

bow = Item(
  char="}",
  color=(0, 191, 255),
  name="Long bow",
  equippable=equippable.RangedWeapon(
    range=1,
    power=3,
  )
)

dagger = Item(
  char="/",
  color=(0, 191, 255),
  name="Rusty dagger",
  equippable=equippable.Equippable(
    equipment_type=equipment_types.EquipmentType.MELEE_WEAPON,
    power_bonus=1,
    defense_bonus=0,
    durability=20,
  )
)

short_sword = Item(
  char="/",
  color=(0, 191, 255),
  name="Short sword",
  equippable=equippable.Equippable(
    equipment_type=equipment_types.EquipmentType.MELEE_WEAPON,
    power_bonus=2,
    defense_bonus=1,
    durability=20,
  )
)


leather_armor = Item(
  char="[",
  color=(139, 69, 19),
  name="Leather armor",
  equippable=equippable.Equippable(
    equipment_type=equipment_types.EquipmentType.ARMOR,
    power_bonus=0,
    defense_bonus=1,
    durability=10,
  )
)

chain_mail = Item(
  char="[",
  color=(139, 69, 19),
  name="Chain mail",
  equippable=equippable.Equippable(
    equipment_type=equipment_types.EquipmentType.ARMOR,
    power_bonus=0,
    defense_bonus=2,
    durability=20,
  )
)