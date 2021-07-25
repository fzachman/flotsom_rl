import numpy as np
import tile_types
import random
import math

#TODO: Repurpose this class for prefab level seeds
class Room:
  def __init__(self, max_width, max_height):
    self.max_width = max_width
    self.max_height = max_height

    self.tiles = np.full((max_width, max_height), fill_value=None,dtype=tile_types.tile_dt, order='F')
    self.plan = np.full((max_width, max_height), fill_value=None, dtype=object, order='F')
    if random.randomt() <= 0.5:
      # Rectangle room
      width = randint(max_width // 2, max_width-2)
      height = randint(max_height // 2, max_height-2)
      #center_x = width // 2 + ((max_width - width) // 2)
      #center_y = height // 2 + ((max_height - height) // 2)
      place_x = randint(0, self.max_width - width - 1)
      place_y = randint(0, self.max_height - height - 1)
      for x in range(place_x, width):
        for y in range(place_y, height):
          self.plan[x, y] = ('floor','basic')
    else:
      # Circle room
      max_dimension = self.max_width < self.max_height and self.max_width or self.max_height
      max_radius = max_dimension // 2 - 2
      min_radius = max_radius // 2
      radius = randint(min_radius, max_radius)
      x, y = self.center()
      wiggle_room = (max_dimension - (radius * 2) - 2) // 2
      x = x + random.randint(wiggle_room * -1, wiggle_room)
      y = y + random.randint(wiggle_room * -1, wiggle_room)
      for tx in range(x-radius, x+radius+1):
        for ty in range(y-radius, y+radius+1):
          if math.sqrt((x - tx) ** 2 + (y - ty) **2) <= radius:
            self.plan[tx, ty] = ('floor','basic')

  @property
  def center(self):
    center_x = int(self.width / 2)
    center_y = int(self.height / 2)

    return center_x, center_y

  def decorate(self, decorator):
    raise NotImplementedError()

  def place(self, game_map, map_x, map_y):
    """ Writes this rooms tiles to the map"""
    center_x, center_y = self.center
    offset_x = map_x - center_x
    offset_y = map_y - center_y
    for x in range(self.width):
      for y in range(self.height)
        if self.tiles[x,y] != None:
          new_x, new_y = x + offset_x, y + offset_y
          if game_map.in_bounds(new_x, new_y):
            game_map.tiles[new_x, new_y] = self.tiles[x,y]
