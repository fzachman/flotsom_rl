import random
import math
from enum import Enum, auto

import tile_types
import tile_bit_codes
from brushes import load_brushes
from entity_factories import light

brush_sets = load_brushes()

class SectorPurpose(Enum):
  COMMAND = auto()
  ENGINEERING = auto()
  SCIENCE = auto()
  SECURITY = auto()
  CREW = auto()


class Sector:
  def __init__(self, x, y, width, height, purpose, brush_set, tile_set, is_destroyed=False):
    self.x = x
    self.y = y
    self.width = width
    self.height = height
    self.purpose = purpose
    self.brush_set = brush_set
    self.tile_set = tile_set
    self.is_destroyed = is_destroyed

class Ship:
  def __init__(self, tile_set):
    self.sectors = []
    self.tile_set = tile_set
    self.tint = tint = (0, random.randint(0,20), random.randint(0,20))
    #print(f'Tint: {tint}')
    # Slight palette shift to make each ship slightly different color
    for tile_type in tile_set.all_tile_types:
      if tile_type['tile_class'] != 'space':
        for l in ('dark','light'):
          old_c = tile_type[l]['bg']
          new_c = old_c[0] + tint[0], old_c[1] + tint[1], old_c[2] + tint[2]
          print(new_c)
          tile_type[l]['bg'] = new_c
    self.protected_zones = []
    self.setup()



  def is_protected(self, x, y):
    for x1, y1, x2, y2 in self.protected_zones:
      if x1 <= x <= x2 and y1 <= y <= y2:
        return True
    return False

  def setup(self):
    # Set our width and height here
    pass

  def pre_gen(self, tiles):
    # Do any kind of setup before we do the procgen stuff,
    # like setting up a main hallway or anything
    pass

  def get_sectors(self):
    # Break up the map however this ship does, then return each
    # block for the procgen to work on.  Should return the size/location
    # of the tiles, along with a brush set to use to generate them.
    # Probably store each sector along with purpose for later/decorate step
    pass

  def post_gen(self, tiles):
    # Stuff to do after the map has been procgenned, but before we
    # go through the room/door process.  Like stamping out a circle in
    # one or more sectors, or joining sectors to the main
    # hall with airlocks,, etc...
    pass

  def decorate(self, dungeon):
    # Add interesting stuff to each room based on its purpose.
    for x in range(1, dungeon.width-1):
      for y in range(1, dungeon.height-1):
        if dungeon.tiles[x, y]['tile_class'] == 'wall':

          tiles = dungeon.tiles[x-1:x+2, y-1:y+2]
          bit_code = tile_bit_codes.get_tile_bit_code(tiles)
          if bit_code != 255:
            #print(f'{tiles} = {bit_code}')
            subclass = tile_bit_codes.get_wall_subclass_for_bit_code(bit_code)
            if subclass:
              new_tile_type = self.tile_set.get_tile_type('wall', subclass)
              if new_tile_type:
                dungeon.tiles[x, y] = new_tile_type





class HallShip(Ship):

  def setup(self):
    """ Hall Ships consist of one long hall, connecting multiple sectors. """
    self.sector_width = (5 * random.randint(4,8)) + 2
    self.sector_height = (5 * random.randint(4,8))
    print(f'Sector Width: {self.sector_width}, Sector height: {self.sector_height}')
    self.ship_length_in_sectors = random.randint(2,120 // self.sector_width)

    self.width = self.sector_width * self.ship_length_in_sectors + 1
    if self.width < 80:
      self.width = 80
    self.height = (self.sector_height * 2) + 16

    for i in range(self.ship_length_in_sectors):
      for y in (0,self.sector_height + 15):
        sector_purpose = random.choice(list(SectorPurpose))
        if sector_purpose in (SectorPurpose.SCIENCE, SectorPurpose.COMMAND):
          brush_set = brush_sets.get('round')
        elif sector_purpose == SectorPurpose.ENGINEERING:
          brush_set = brush_sets.get('warty')
        else:
          brush_set = brush_sets.get('default')

        is_destroyed = random.random() <= .1

        self.sectors.append(Sector(i * self.sector_width,
                                    y,
                                    self.sector_width,
                                    self.sector_height,
                                    sector_purpose,
                                    brush_set,
                                    self.tile_set,
                                    is_destroyed=is_destroyed
                                    ))

  def pre_gen(self, tiles):
    # The hall itself is 3 tiles wide + 1 wall tile on each side for 5 tiles total.
    # The hall will connect to each section of ship by another 3/5 wide hall tile.
    midline_y = self.sector_height + 8
    #import pdb; pdb.set_trace()
    tiles[3:(self.sector_width * self.ship_length_in_sectors) - 3, midline_y-1: midline_y+2] = self.tile_set.get_tile_type('floor', 'basic')
    self.protected_zones.append((0,midline_y-10, self.width - 1, midline_y + 10))

    for i in range(self.ship_length_in_sectors):
      # Generate an airlock to connect the main hall to each sector
      midline_x = (self.sector_width * i) + (self.sector_width // 2)
      end_x     = (self.sector_width * i) + self.sector_width
      print(f'Midline Y: {midline_y}, -3: {midline_y-3}, -20: {midline_y - 20}')
      if random.random() < .1:
        # Generate a blocked off entrance to this sector.  Pathing should create an alternate
        # route from a neighboring sector
        tiles[midline_x-1:midline_x+2, midline_y-5:midline_y-2] = self.tile_set.get_tile_type('floor', 'basic')
        tiles[midline_x-1:midline_x+2,midline_y-5] = self.tile_set.get_tile_type('wall', 'damaged')
        tiles[midline_x + random.randint(-1,1),midline_y-4] = self.tile_set.get_tile_type('wall', 'damaged')
      else:
        tiles[midline_x-1:midline_x+2, midline_y-20:midline_y-2] = self.tile_set.get_tile_type('floor', 'basic')

      if random.random() < .1:
        # Generate a blocked off entrance to this sector.  Pathing should create an alternate
        # route from a neighboring sector
        tiles[midline_x-1:midline_x+2, midline_y+3:midline_y+6] = self.tile_set.get_tile_type('floor', 'basic')
        tiles[midline_x-1:midline_x+2,midline_y+5] = self.tile_set.get_tile_type('wall', 'damaged')
        tiles[midline_x + random.randint(-1,1),midline_y+4] = self.tile_set.get_tile_type('wall', 'damaged')
      else:
        tiles[midline_x-1:midline_x+2, midline_y+3:midline_y+20] = self.tile_set.get_tile_type('floor', 'basic')

      # Doors to access the sector airlocks
      tiles[midline_x, midline_y - 2] = self.tile_set.get_tile_type('door')
      tiles[midline_x, midline_y + 2] = self.tile_set.get_tile_type('door')

      if i < self.ship_length_in_sectors - 1:
        tiles[end_x-1:end_x+2, midline_y - 1] = self.tile_set.get_tile_type('wall', 'basic')
        tiles[end_x, midline_y] = self.tile_set.get_tile_type('door', 'closed')
        tiles[end_x-1:end_x+2, midline_y + 1] = self.tile_set.get_tile_type('wall', 'basic')

  def post_gen(self, tiles):
    # Add these here so they don't trigger doors
    midline_y = self.sector_height + 8
    for x in range(2,5):
      for y in range(-1,2):
        if x == 2 or random.random() <.5:
          tiles[x,midline_y + y] = self.tile_set.get_tile_type('wall', 'damaged')
        if x == 2 or random.random() <.5:
          tiles[(self.sector_width * self.ship_length_in_sectors) - x - 1,midline_y+y] = self.tile_set.get_tile_type('wall', 'damaged')



class SphereStarShip(Ship):

  def setup(self):
    """ SphereStarShips consist of one central circular sector surrounded by other circles. """
    self.sector_width = (5 * random.randint(4,6))
    self.sector_height = self.sector_width
    print(f'Sector Width: {self.sector_width}, Sector height: {self.sector_height}')

    self.width = self.sector_width * 3
    if self.width < 80:
      self.width = 80
    self.height = self.width

    for i in range(3):
      for j in range(3):
        x = i * self.sector_width
        y = j * self.sector_height
        sector_purpose = random.choice(list(SectorPurpose))
        if sector_purpose in (SectorPurpose.SCIENCE, SectorPurpose.COMMAND):
          brush_set = brush_sets.get('round')
        elif sector_purpose == SectorPurpose.ENGINEERING:
          brush_set = brush_sets.get('warty')
        else:
          brush_set = brush_sets.get('default')

        is_destroyed = random.random() <= .15

        self.sectors.append(Sector(x,
                                    y,
                                    self.sector_width,
                                    self.sector_height,
                                    sector_purpose,
                                    brush_set,
                                    self.tile_set,
                                    is_destroyed=is_destroyed
                                    ))

  def post_gen(self, tiles):
    # Add these here so they don't trigger doors
    radius = (self.sector_width // 2 ) - 2
    for i in range(3):
      for j in range(3):
        start_x, start_y = (self.sector_width * i), (self.sector_height * j)
        end_x, end_y     = start_x + self.sector_width, start_y + self.sector_height
        center_x = (self.sector_width * i) + (self.sector_width // 2)
        center_y = (self.sector_height * j) + (self.sector_height // 2)

        for x in range(start_x, end_x):
          for y in range(start_y, end_y):
            if math.sqrt((center_x - x) ** 2 + (center_y - y) **2) > radius:
              tiles[x,y] = self.tile_set.get_tile_type('wall', 'basic')

    for i in range(3):
      for j in range(3):
        # Join each group
        center_x = (self.sector_width * i) + (self.sector_width // 2)
        center_y = (self.sector_height * j) + (self.sector_height // 2)
        if i < 2:
          # Connect to sphere to our right
          tiles[(self.sector_width * (i+1)) - 3:(self.sector_width * (i+1))+3, center_y-1:center_y+2] = self.tile_set.get_tile_type('floor', 'basic')
          tiles[(self.sector_width * (i+1)) - 3, center_y-2:center_y+3] = self.tile_set.get_tile_type('wall','basic')
          tiles[(self.sector_width * (i+1)) - 3, center_y] = self.tile_set.get_tile_type('door')
          tiles[(self.sector_width * (i+1)) + 3, center_y-2:center_y+3] = self.tile_set.get_tile_type('wall','basic')
          tiles[(self.sector_width * (i+1)) + 3, center_y] = self.tile_set.get_tile_type('door')

        if j < 2:
          # Connect to sphere below us
          tiles[center_x-1:center_x+2, (self.sector_height * (j+1)) - 3:(self.sector_height * (j+1)) +3] = self.tile_set.get_tile_type('floor', 'basic')
          tiles[center_x-2:center_x+3,(self.sector_height * (j+1)) - 3] = self.tile_set.get_tile_type('wall','basic')
          tiles[center_x,(self.sector_height * (j+1)) - 3] = self.tile_set.get_tile_type('door')
          tiles[center_x-2:center_x+3,(self.sector_height * (j+1)) + 3] = self.tile_set.get_tile_type('wall','basic')
          tiles[center_x,(self.sector_height * (j+1)) + 3] = self.tile_set.get_tile_type('door')
