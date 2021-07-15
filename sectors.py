import numpy as np
import random

import tile_types

class SectorTemplate:
  """ A single sector template of a game map.
  Contains an array of tile types and a size.
  width and height must be divisible by 3 to allow an even division into
  subsectors"""
  def __init__(self, width, height, name='<Unnamed>'):
    self.name = name
    self.width = width
    self.height = height
    # Create a blank sector filled with walls.  We will place floor, transition and hall tiles
    # throughout.
    self.tiles = np.full((width, height), fill_value=tile_types.wall, order='F')

    self.subsector_width = self.width // 3
    self.subsector_height = self.height // 3
    return

  def randomize(self):
    tiles = self.tiles
    for i in range(4):
      if random.random() <= 0.5:
        transform = random.choice([np.rot90, np.fliplr, np.flipud])
        tiles = transform(tiles)
    return tiles.copy()

class SectorExitMap:
  def __init__(self, tiles):
    self.tiles = tiles
    self.north_exits = []
    self.east_exits = []
    self.south_exits = []
    self.west_exits = []

    height = len(tiles)
    width = len(tiles[0])
    for x in range(width):
      if x == 0:
        for y in range(height):
          if tiles[x,y] == tile_types.exit_point:
            self.west_exits.append((x,y))
      elif x == width - 1:
        for y in range(height):
          if tiles[x,y] == tile_types.exit_point:
            self.east_exits.append((x,y))

      if tiles[x,0] == tile_types.exit_point:
        self.north_exits.append((x,0))
      if tiles[x,height-1] == tile_types.exit_point:
        self.south_exits.append((x, height - 1))
    print(f'Sector has N:{len(self.north_exits)}, E:{len(self.east_exits)}, S:{len(self.south_exits)}, W:{len(self.west_exits)}')
