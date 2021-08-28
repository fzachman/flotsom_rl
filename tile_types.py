import numpy as np
import random
from enum import Enum, auto

class TileClass(Enum):
  FLOOR = auto()
  WALL = auto()
  DOOR = auto()
  OBSTACLE = auto()
  INTERACTABLE = auto()

class TileSubclass(Enum):
  BASIC = auto()
  DAMAGED = auto()
  HALL = auto()
  OPEN = auto()
  CLOSED = auto()
  STORAGE = auto()
  TRIGGER = auto()
  EXIT = auto()

# Tile graphics structured type compatible with Console.tiles_rgb
graphic_dt = np.dtype(
  [
    ('ch', np.int32), #Unicode codepoint
    ('fg', '3B'), # 3 unsigned bytes, for RGB colors
    ('bg', '3B'),
  ]
)

# Tile struct used for statistically defined tile data
tile_dt = np.dtype(
  [
    ('walkable', np.bool), # True if it can be walked over
    ('transparent', np.bool), # True if it doesn't block FOV
    ('dark', graphic_dt), # Graphics for when not in FOV
    ("light", graphic_dt),  # Graphics for when the tile is in FOV.
    ('tile_class', np.unicode_, 16),
    ('tile_subclass', np.unicode_, 16),
    ('weight', np.int8)
  ]
)

def new_tile(*,  # Enforce the use of keywords, so that parameter order doesn't matter.
             walkable,
             transparent,
             dark,
             dim,
             light,
             tile_class,
             tile_subclass,
             weight):
    """Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light, tile_class,tile_subclass,weight), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(' '), (255,255,255), (0,0,0)), dtype=graphic_dt)

class TileSet:
  def __init__(self):
    self.all_tile_types = []
    self.tile_classes = {'floor': {'basic': [],
                                   'damaged': []},
                         'wall': {'basic': [],
                                  'damaged': [],},
                         'door': {'open': [],
                                  'closed': [],},
                         'obstacle': {'basic': []},
                         'interactable': {'storage': [],
                                          'triggers': [],
                                          'exit': []},
                          }

  def copy(self):
    tile_set = TileSet()
    for tile_class, tile_subclasses in self.tile_classes.items():
      for tile_subclass, tiles in tile_subclasses.items():
        for tile in tiles:
          tile_set.add_tile_type(tile_class, tile_subclass,
                                 tile['walkable'],
                                 tile['transparent'],
                                 tile['dark'],
                                 tile['light'],
                                 tile['weight'])
    return tile_set

  def is_tile_class(self, tile_type, tile_class, tile_subclass=None):
    """ Check to see if the passed in tile is part of a tile_class """
    tile_types = []
    if tile_subclass:
      tile_types = self.tile_classes.get(tile_class, {}).get(tile_subclass, [])
    else:
      for tile_subclass, sub_types in self.tile_classes.get(tile_class, {}).items():
        tile_types.extend(sub_types)
    return tile_type in tile_types

  def get_tile_type(self, tile_class, tile_subclass=None):
    tile_subclasses = self.tile_classes.get(tile_class, {})
    if tile_subclass:
      options = tile_subclasses.get(tile_subclass, [])
    else:
      # Choose from all tile_subclasses, useful for randomly selecting
      # open/closed doors
      options = []
      for k, v in tile_subclasses.items():
        options.extend(v)

    if options:
      chosen = random.choices(
        options, weights=[o['weight'] for o in options], k=1
      )
      if chosen:
        return chosen[0]
      else:
        return None
    else:
      print(f'No options for tile class {tile_class}:{tile_subclass}')
      return None

  def add_tile_type(self,
                    tile_class,
                    tile_subclass,
                    walkable,
                    transparent,
                    dark,
                    light,
                    weight):
    tile_type = np.array((walkable, transparent, dark, light, tile_class,tile_subclass,weight), dtype=tile_dt)
    tile_subclasses = self.tile_classes.setdefault(tile_class, {})
    tile_types = tile_subclasses.setdefault(tile_subclass, [])
    tile_types.append(tile_type)
    self.all_tile_types.append(tile_type)


basic_floor_fg_dark = (255,255,255)
basic_floor_bg_dark = (30,30,30)
basic_floor_fg_light = (255,255,255)
basic_floor_bg_light = (200,200,200)

basic_wall_fg_dark = (135,135,145)
basic_wall_bg_dark = (20,20,30)
basic_wall_fg_light = (230,230,230)
basic_wall_bg_light = (100,100,100)

basic_tile_set = TileSet()
##########
# FLOORS #
##########
basic_tile_set.add_tile_type(tile_class='floor', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(ord(' '), basic_floor_fg_dark, basic_floor_bg_dark),
                             light=(ord(' '), basic_floor_fg_light, basic_floor_bg_light),
                             weight=10
                             )
basic_tile_set.add_tile_type(tile_class='floor', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(9617, (20,20,20), basic_floor_bg_dark),
                             light=(9617, (180, 180, 180), basic_floor_bg_light),
                             weight=1
                             )

#########
# WALLS #
#########
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='basic',
                             walkable=False, transparent=False,
                             dark=(ord(' '), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord(' '), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)

basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='damaged',
                             walkable=False, transparent=False,
                             dark=(9617, (10,10,10),(20,20,20)),
                             light=(9617, (70, 70, 70), (100, 100, 100)),
                             weight=10,)

###################
# DECORATED WALLS #
###################
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='h',
                             walkable=False, transparent=False,
                             dark=(ord('║'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('║'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='v',
                             walkable=False, transparent=False,
                             dark=(ord('═'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('═'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='dr',
                             walkable=False, transparent=False,
                             dark=(ord('╔'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╔'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='dl',
                             walkable=False, transparent=False,
                             dark=(ord('╗'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╗'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='ur',
                             walkable=False, transparent=False,
                             dark=(ord('╚'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╚'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='ul',
                             walkable=False, transparent=False,
                             dark=(ord('╝'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╝'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='tr',
                             walkable=False, transparent=False,
                             dark=(ord('╠'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╠'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='tl',
                             walkable=False, transparent=False,
                             dark=(ord('╣'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╣'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='td',
                             walkable=False, transparent=False,
                             dark=(ord('╦'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╦'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='tu',
                             walkable=False, transparent=False,
                             dark=(ord('╩'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╩'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)
basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='x',
                             walkable=False, transparent=False,
                             dark=(ord('╬'), basic_wall_fg_dark,basic_wall_bg_dark),
                             light=(ord('╬'), basic_wall_fg_light, basic_wall_bg_light),
                             weight=10,)



basic_tile_set.add_tile_type(tile_class='wall', tile_subclass='glass',
                             walkable=False, transparent=True,
                             dark=(ord('G'), (0,0,0),(20,20,20)),
                             light=(ord('G'), (255, 255, 255), (100, 100, 100)),
                             weight=10,)

basic_tile_set.add_tile_type(tile_class='door',tile_subclass='open',
                             walkable = True, transparent = True,
                             dark=(ord('_'), (70,70,70), (30,30,30)),
                             light=(ord('_'), (255, 255, 255), (200, 200, 200)),
                             weight=20,
                             )

basic_tile_set.add_tile_type(tile_class='door',tile_subclass='closed',
                             walkable = False, transparent = False,
                             dark=(ord('#'), (70,70,70), (30,30,30)),
                             light=(ord('#'), (255, 255, 255), (190, 190, 190)),
                             weight=10,
                             )

basic_tile_set.add_tile_type(tile_class='interactable',tile_subclass='exit',
                             walkable=True,transparent=True,
                             dark=(ord('>'), (0, 0, 50), (0,0,100)),
                             light=(ord('>'), (255,255,255),(200,180,50)),
                             weight=10,
                             )

###################################
# SPAAAAAAAAAAAAAAAAAAAAAAAAAAACE #
###################################
basic_tile_set.add_tile_type(tile_class='space', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(ord(' '), (0,0,0), (0,0,0)),
                             light=(ord(' '), (0,0,0), (0,0,0)),
                             weight=40
                             )
basic_tile_set.add_tile_type(tile_class='space', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(ord('.'), (50,50,50), (0,0,0)),
                             light=(ord('.'), (180,180,180), (0,0,0)),
                             weight=5
                             )
basic_tile_set.add_tile_type(tile_class='space', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(ord('.'), (80,80,80), (0,0,0)),
                             light=(ord('.'), (220,220,220), (0,0,0)),
                             weight=2
                             )
basic_tile_set.add_tile_type(tile_class='space', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(183, (50,50,50), (0,0,0)),
                             light=(183, (180,180,180), (0,0,0)),
                             weight=5
                             )

basic_tile_set.add_tile_type(tile_class='space', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(183, (80,80,80), (0,0,0)),
                             light=(183, (220,220,220), (0,0,0)),
                             weight=2
                             )

basic_tile_set.add_tile_type(tile_class='space', tile_subclass='basic',
                             walkable=True, transparent=True,
                             dark=(ord('*'), (80,80,80), (0,0,0)),
                             light=(ord('*'), (220,220,220), (0,0,0)),
                             weight=1
                             )
tile_sets = (basic_tile_set)
