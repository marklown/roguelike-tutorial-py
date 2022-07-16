from components.ai import HostileEnemy
from components.consumable import (
  HealingConsumable,
  LightningDamageConsumable,
  ConfusionConsumable,
  FireballDamageConsumable,
)
from components.fighter import Fighter
from components.inventory import Inventory
from entity import Actor, Item

player = Actor(
  char="@", 
  color=(255, 255, 255), 
  name="Player", 
  ai_cls=HostileEnemy, # Doesn't actually use the AI, but ai_cls is required for all actors
  fighter=Fighter(hp=30, defense=2, power=5),
  inventory=Inventory(capacity=26)
)

orc = Actor(
  char="o", 
  color=(63, 127, 63), 
  name="Orc", 
  ai_cls=HostileEnemy,
  fighter=Fighter(hp=10, defense=0, power=3),
  inventory=Inventory(capacity=0)
)

troll = Actor(
  char="T", 
  color=(0, 127, 0), 
  name="Troll", 
  ai_cls=HostileEnemy,
  fighter=Fighter(hp=16, defense=1, power=4),
  inventory=Inventory(capacity=0)
)



health_potion = Item(
  char="!",
  color=(127, 0, 255),
  name="Potion of Healing",
  consumable=HealingConsumable(amount=4)
)

lightning_scroll = Item(
  char="~",
  color=(255, 255, 0),
  name="Scroll of Lightning",
  consumable=LightningDamageConsumable(damage=20, max_range=5)
)

confusion_scroll = Item(
  char="~",
  color=(207, 63, 255),
  name="Scroll of Confusion",
  consumable=ConfusionConsumable(number_of_turns=10)
)

fireball_scroll = Item(
  char="~",
  color=(255, 0, 0),
  name="Scroll of Conflagration",
  consumable=FireballDamageConsumable(damage=12, radius=3)
)

