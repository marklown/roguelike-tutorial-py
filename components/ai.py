from __future__ import annotations
from typing import List, Optional, Tuple, TYPE_CHECKING
import numpy as np
import tcod
import random

from actions import (
  Action, 
  BumpAction,
  MeleeAction, 
  MovementAction, 
  WaitAction
)

if TYPE_CHECKING:
  from entity import Actor

class BaseAI(Action):

  def perform(self) -> None:
    raise NotImplementedError()

  def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
    """Compute and return a path to the target position. If there is no
    value path then return an empty list"""
    # Copy the walkable array
    cost = np.array(self.entity.game_map.tiles["walkable"], dtype=np.int8)

    for entity in self.entity.game_map.entities:
      # Check that an entity blocks movement and the cost isn't zero
      if entity.blocks_movement and cost[entity.x, entity.y]:
        # Add to the cost of a blocked position
        # A lower number means more enemies will crowd behind each other,
        # a higher number means enemies will take longer paths in order
        # to surround the player
        cost[entity.x, entity.y] += 10

    # Create a graph from the cost array and pass that graph to a pathfinder
    graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=0) # diagonal=0 means cardinal moves only
    pathfinder = tcod.path.Pathfinder(graph)
    pathfinder.add_root((self.entity.x, self.entity.y)) # start position

    # compute the path to the destination and remove the starting point
    path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

    # convert from List[List[int]] to List[Tuple[int, int]]
    return [(index[0], index[1]) for index in path]


class HostileEnemy(BaseAI):
  def __init__(self, entity: Actor):
    super().__init__(entity)
    self.path: List[Tuple[int, int]] = []
    self.sleeping = True

  def perform(self) -> None:
    target = self.engine.player
    dx = target.x - self.entity.x
    dy = target.y - self.entity.y
    distance = max(abs(dx), abs(dy)) # Dhebyshev distance

    if self.engine.game_map.visible[self.entity.x, self.entity.y]:
      if distance <= 4:
        self.sleeping = False
      if distance <= 1:
        if dx == 0 or dy == 0: # Only attack in cardinal directions
          return MeleeAction(self.entity, dx, dy).perform()
      if not self.sleeping:
        self.path = self.get_path_to(target.x, target.y)

    if self.path:
      dest_x, dest_y = self.path.pop(0)
      return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

    return WaitAction(self.entity).perform()


class ConfusedEnemy(BaseAI):
  def __init__(self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int) -> None:
    super().__init__(entity)
    self.previous_ai = previous_ai
    self.turns_remaining = turns_remaining

  def perform(self) -> None:
    if self.turns_remaining <= 0:
      self.engine.message_log.add_message(f"The {self.entity.name} is no longer confused")
      self.entity.ai = self.previous_ai
    else:
      x, y = random.choice(
        [
          (0, -1),
          (-1, 0),
          (1, 0),
          (0, 1),
        ]
      )
      self.turns_remaining -= 1
      return BumpAction(self.entity, x, y).perform()