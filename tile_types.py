from typing import Tuple
import random
import numpy as np # type: ignore

# Tile graphics structured type compatible with Console.tiles_rgb
graphic_dt = np.dtype(
  [
    ("ch", np.int32), # Unicode codepoint
    ("fg", "3B"),     # 3 unsigned bytes, for RGB colors
    ("bg", "3B")
  ]
)

# Tile struct used for statically defined tile data
tile_dt = np.dtype(
  [
    ("walkable", np.bool),    # True if this tile can be walked on
    ("transparent", np.bool), # True if this tile does not block FOV
    ("dark", graphic_dt),     # Graphics for when this tile is not in FOV
    ("light", graphic_dt),    # Graphics for when this tile in in FOV
  ]
)

def new_tile(
  *,
  walkable: int,
  transparent: int,
  dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
  light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
  """
  Helper function for defining a new tile type
  """
  return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# fog represents unexplored, unseen tiles
fog = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# Floor tile
floor = new_tile(
  walkable=True,
  transparent=True,
  dark=(ord(" "), (22, 36, 51), (9, 12, 17)),
  light=(ord(" "), (9, 12, 17), (22, 36, 51)),
)

# Wall tile
wall = new_tile(
  walkable=False,
  transparent=False,
  dark=(ord("#"), (44, 64, 72), (22, 32, 36)),
  light=(ord("#"), (22, 32, 36), (126, 149, 156)),
)

stairs_down = new_tile(
  walkable=True,
  transparent=True,
  dark=(ord(">"), (44, 64, 72), (22, 32, 36)),
  light=(ord(">"), (22, 32, 36), (126, 149, 156)),
)
