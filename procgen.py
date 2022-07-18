from __future__ import annotations
import random
from typing import Iterator, List, Tuple, TYPE_CHECKING
from numpy import diff, tile
import tcod
from game_map import GameMap
import tile_types
import difficulty

if TYPE_CHECKING:
  from engine import Engine
  from entity import Entity

class RectangularRoom:
  def __init__(self, x: int, y: int, width: int, height: int) -> None:
    self.x1 = x
    self.y1 = y
    self.x2 = x + width
    self.y2 = y + height

  @property
  def center(self) -> Tuple[int, int]:
    center_x = int((self.x1 + self.x2) / 2)
    center_y = int((self.y1 + self.y2) / 2)
    return center_x, center_y

  @property
  def inner(self) -> Tuple[slice, slice]:
    # Return the inner area of this room as a 2D array index
    return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

  def intersects(self, other: RectangularRoom) -> bool:
    # Return True if this room overlaps with another
    return (
      self.x1 <= other.x2 and
      self.x2 >= other.x1 and
      self.y1 <= other.y2 and
      self.y2 >= other.y1
    )


def place_entities(
  room: RectangularRoom,
  dungeon: GameMap,
  floor_number: int,
) -> None:
  # Place entities in the given room
  number_of_monsters = random.randint(
    0, difficulty.get_max_value_by_floor(difficulty.max_monsters_by_floor, floor_number)
  )
  number_of_items = random.randint(
    0, difficulty.get_max_value_by_floor(difficulty.max_items_by_floor, floor_number)
  )

  monsters: List[Entity] = difficulty.get_random_entities_by_floor(
    difficulty.enemy_chances, number_of_monsters, floor_number
  )

  items: List[Entity] = difficulty.get_random_entities_by_floor(
    difficulty.item_chances, number_of_items, floor_number
  )

  for entity in monsters + items:
    x = random.randint(room.x1 + 1, room.x2 - 1)
    y = random.randint(room.y1 + 1, room.y2 - 1)
    if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
      entity.spawn(dungeon, x, y)


def tunnel_between(
  start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
  # Return an L-shaped tunnel between these two points
  x1, y1 = start
  x2, y2 = end
  if random.random() < 0.5:
    # Move horizontally, then vertically
    corner_x, corner_y = x2, y1
  else:
    # Move vertically, then horizontally
    corner_x, corner_y = x1, y2

  # Generate the coordiates for this tunnel
  for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
    yield x, y
  for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
    yield x, y

def generate_dungeon(
  max_rooms: int,
  room_min_size: int,
  room_max_size: int,
  map_width: int,
  map_height: int,
  engine: Engine
) -> GameMap:
  # Generate a new dungeon game map
  player = engine.player
  dungeon = GameMap(engine, map_width, map_height, entities=[player])

  rooms: List[RectangularRoom] = []
  center_of_last_room = (0, 0) # Keep track of center of last room so we can place stairs there

  for r in range(max_rooms):
    room_width = random.randint(room_min_size, room_max_size)
    room_height = random.randint(room_min_size, room_max_size)

    x = random.randint(0, dungeon.width - room_width - 1)
    y = random.randint(0, dungeon.height - room_height - 1)

    new_room = RectangularRoom(x, y, room_width, room_height)

    # Run through the other rooms and see if they intersect with this one
    if any(new_room.intersects(other_room) for other_room in rooms):
      continue # THis room intersects, try again

    # Dig out this rooms inner area
    dungeon.tiles[new_room.inner] = tile_types.floor

    if len(rooms) == 0:
      # The first room is where the player starts
      player.place(*new_room.center, dungeon)
    else:
      # Dig a tunnel between this room and the previous one
      for x, y in tunnel_between(rooms[-1].center, new_room.center):
        dungeon.tiles[x, y] = tile_types.floor
      center_of_last_room = new_room.center

    place_entities(new_room, dungeon, engine.game_world.current_floor)

    # Place stairs leading down in the center of the last room
    dungeon.tiles[center_of_last_room] = tile_types.stairs_down
    dungeon.stairs_down_location = center_of_last_room

    rooms.append(new_room)

  return dungeon
