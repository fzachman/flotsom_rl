import numpy as np
import random
import math
from tcod.console import Console

from entity import Actor, Item, Container
import tile_types

class GameMap:
  def __init__(self, engine, width, height, tile_set, entities=()):
    self.engine = engine
    self.width, self.height = width, height
    self.entities = set(entities)
    self.tile_set = tile_set
    self.tiles = np.full((width, height), fill_value=tile_set.get_tile_type('wall','basic'), order='F')
    #self.vacuum = np.full((width, height), fill_value=False, order="F")  # Tiles that are in vacuum
    self.visible = np.full((width, height), fill_value=False, order="F")  # Tiles the player can currently see
    self.light_levels = np.full((width, height), fill_value=1.0, order="F")  # Tiles the player can currently see
    self.explored = np.full((width, height), fill_value=False, order="F")  # Tiles the player has seen before
    self.downstairs_location = (0,0)
    self._rooms = []
    self.room_lookup = {}
    self.vacuum_sources = []
    self.show_debug = False
    self.vacuum_tiles = set()

  @property
  def rooms(self):
    return self._rooms

  @rooms.setter
  def rooms(self, rooms):
    self._rooms = rooms
    self.room_lookup = {}
    self.vacuum_sources = []
    for r in rooms:
      for xy in r.coords:
        self.room_lookup[xy] = r
      if r.is_vacuum_source:
        self.vacuum_sources.append(r)

  def add_room(self, new_room):
    new_rooms = self._rooms.copy()
    new_rooms.append(new_room)
    self.rooms = new_rooms

  def get_room_at_location(self, xy):
    return self.room_lookup.get(xy)

  @property
  def gamemap(self):
    return self

  @property
  def actors(self):
    """Iterate over this maps living actors"""

    yield from(entity for entity in self.entities if isinstance(entity, Actor) and entity.is_alive)

  @property
  def items(self):
    yield from(entity for entity in self.entities if isinstance(entity, Item))

  @property
  def lights(self):
    yield from(entity for entity in self.entities if entity.light_source and entity.light_source.radius > 0)


  def reveal_map(self):
    self.explored = np.full((self.width, self.height), fill_value=True, order="F")

  def get_blocking_entity_at_location(self, location_x, location_y):
    for entity in self.entities:
      if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
        return entity

    return None

  def get_actor_at_location(self, x, y):
    for actor in self.actors:
      if actor.x == x and actor.y == y:
        return actor
    return None

  def in_bounds(self, x, y):
    """Return True if x and y in arinsde of the bounds of this map"""
    return 0 <= x < self.width and 0 <= y < self.height

  def get_coords_in_radius(self, x, y, radius):
    coords = []
    for tx in range(x-radius, x+radius+1):
      for ty in range(y-radius, y+radius+1):
        if math.sqrt((x - tx) ** 2 + (y - ty) **2) <= radius and \
              self.in_bounds(tx, ty):
          coords.append((tx,ty))
    return coords

  def get_viewport(self):
    x = self.engine.player.x
    y = self.engine.player.y
    width = self.engine.game_world.viewport_width
    height = self.engine.game_world.viewport_height
    half_width = int(width / 2)
    half_height = int(height / 2)
    origin_x = x - half_width
    origin_y = y - half_height
    #print(f'player: ({x}, {y}), modifier: {half_width}, {half_height}, origin: ({origin_x}, {origin_y})')
    if origin_x < 0:
      origin_x = 0
    if origin_y < 0:
      origin_y = 0


    end_x = origin_x + width
    end_y = origin_y + height
    #print(f'End: ({end_x},{end_y})')
    if end_x > self.width:
      x_diff = end_x - self.width
      origin_x -= x_diff
      end_x    -= x_diff

    if end_y > self.height:
      y_diff = end_y - self.height
      origin_y -= y_diff
      end_y    -= y_diff
    return ((origin_x, origin_y, end_x-1, end_y-1))

  def render(self, console):
    """
    Renders the map.

    If a tile is in the "visible" array, then draw it with the "light" colors.
    If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
    Otherwise, the default is "SHROUD".
    """
    o_x, o_y, e_x, e_y = self.get_viewport()
    s_x = slice(o_x, e_x+1)
    s_y = slice(o_y,e_y+1)
    viewport_tiles    = self.tiles[s_x,s_y]#[o_x:e_x+1,o_y:e_y + 1]
    viewport_visible  = self.visible[s_x,s_y]
    viewport_explored = self.explored[s_x,s_y]
    #print(f'({o_x},{o_y}), ({e_x},{e_y})')
    #print(f'Viewport Tiles: ({len(viewport_tiles)},{len(viewport_tiles[0])})')
    #print(f'Viewport Dim: ({len(viewport_dim)},{len(viewport_dim[0])})')
    #print(f'Viewport Visible: ({len(viewport_visible)},{len(viewport_visible[0])})')
    #print(f'Viewport Explored: ({len(viewport_explored)},{len(viewport_explored[0])})')
    #console.tiles_rgb[0:self.engine.game_world.viewport_width, 0:self.engine.game_world.viewport_height] = np.select(
    #    condlist=[viewport_visible, viewport_explored],
    #    choicelist=[viewport_tiles["light"], viewport_tiles["dark"]],
    #    default=tile_types.SHROUD
  #  )
    console.tiles_rgb[0:self.engine.game_world.viewport_width, 0:self.engine.game_world.viewport_height] = np.select(
        condlist=[viewport_explored],
        choicelist=[viewport_tiles["dark"]],
        default=tile_types.SHROUD
    )

    player = self.engine.player
    # Add our player light to our light map
    light_levels = self.light_levels.copy()
    #coords = self.get_coords_in_radius(player.x, player.y, player.light_source.radius)
    #light_levels[player.x][player.y] = 1.0
    #for x, y in coords:
    #  distance = player.distance(x, y)
    #  brightness_diff = distance / (player.light_source.radius+2)
    #  #print(f'Player: ({player.x},{player.y}).  Tile: ({x},{y}).  Distance: {distance}.  Brightness Diff: {brightness_diff}')
    #  if brightness_diff < light_levels[x][y]:
    #    light_levels[x][y] = brightness_diff

    viewport_light_levels = light_levels[s_x,s_y]
    visible_light_levels = np.select(condlist=[viewport_visible], choicelist=[viewport_light_levels], default=1)
    # Try some more dynamic lighting
    lit = np.where(visible_light_levels < 1.0)
    #print(f'Player is at ({self.engine.player.x},{self.engine.player.y}).  These tile are lit: {lit}')
    for i in range(len(lit[0])):
      x, y = lit[0][i], lit[1][i]
      brightness_diff = visible_light_levels[x][y]
      #distance = self.engine.player.distance(x + o_x, y + o_y)
      #brightness_diff = distance / (self.engine.player.visibility+2)
      #print(f'({x},{y}) is lit, translated to ({x-o_x},{y-o_y}) in viewport.  Distance to player: {distance}.')
      light_fg = viewport_tiles[x][y]['light']['fg']
      light_bg = viewport_tiles[x][y]['light']['bg']
      dark_fg = viewport_tiles[x][y]['dark']['fg']
      dark_bg = viewport_tiles[x][y]['dark']['bg']
      new_fg = []
      new_bg = []
      for j in range(0,3):
        new_fg.append(light_fg[j] - int((light_fg[j] - dark_fg[j]) * brightness_diff))
        new_bg.append(light_bg[j] - int((light_bg[j] - dark_bg[j]) * brightness_diff))
      #print(f'Light fg:{light_fg}, bg:{light_bg}, Dark fg:{dark_fg}, bg{dark_bg}.  Multiplier: {brightness_diff}.  New fg:{new_fg}, bg:{new_bg}')
      console.tiles_rgb['bg'][x,y] = tuple(new_bg)
      console.tiles_rgb['fg'][x,y] = tuple(new_fg)



    for x,y in self.vacuum_tiles:
      if o_x <= x <= e_x and o_y <= y <= e_y and self.explored[x,y]:
        v_x = x - o_x
        v_y = y - o_y
        r,g,b = console.tiles_rgb['bg'][v_x,v_y]
        r += 20
        if r >= 255:
          r = 255
          g -= 20
          b -= 20
          if g < 0:
            g = 0
          if b < 0:
            b = 0
        console.tiles_rgb['bg'][v_x,v_y] = (r,g,b)


    # Quick room visualizer
    if self.show_debug:
      for room in self.rooms:
        color = room.color
        #print(f'Painting room {color}, ({room.min_x},{room.min_y}),({room.max_x},{room.max_y})')
        for x,y in room.coords:
          if o_x <= x <= e_x and o_y <= y <= e_y:
            console.tiles_rgb['bg'][x-o_x,y-o_y] = color

      # Highlight the exits of the room we're in
      this_room = self.room_lookup.get((self.engine.player.x, self.engine.player.y))
      if this_room:
        for x,y in this_room.exits:
          if o_x <= x <= e_x and o_y <= y <= e_y:
            console.tiles_rgb['bg'][x-o_x,y-o_y] = (255,0,0)
        for room in this_room.connecting_rooms:
          for x,y in room.coords:
            if o_x <= x <= e_x and o_y <= y <= e_y:
              console.tiles_rgb['bg'][x-o_x,y-o_y] = (255,255,255)
    #console.tiles_rgb[0:self.width, 0:self.height] = np.select(
    #    condlist=[self.visible, self.explored],
    #    choicelist=[self.tiles["light"], self.tiles["dark"]],
    #    default=tile_types.SHROUD
    #)
    entities_sorted_for_rendering = sorted(
      self.entities, key=lambda x: x.render_order.value
    )

    for entity in entities_sorted_for_rendering:
      if self.visible[entity.x, entity.y] and light_levels[entity.x][entity.y] < 1:
        console.print(x=entity.x - o_x,
                      y=entity.y - o_y,
                      string=entity.char,
                      fg=entity.color)

class GameWorld:
  """
  Holds the settings for the GameMap and generates new maps when moving down the stairs.
  """

  def __init__(self,
               *,
               engine,
               viewport_width,
               viewport_height,
               current_floor=0):
    self.engine = engine


    self.viewport_width = viewport_width
    self.viewport_height = viewport_height

    self.min_map_width = viewport_width
    self.min_map_height = viewport_height



    self.current_floor = current_floor

  def generate_floor(self):
    self.current_floor += 1
    #map_width = random.randint(self.min_map_width, int(self.min_map_width * 1.25))
    #map_height = random.randint(self.min_map_height, int(self.min_map_height * 1.25))
    #TODO: Choose different tile sets for different ship types
    tile_set = tile_types.basic_tile_set

    #from procgen_wfc import generate_dungeon
    #self.engine.game_map = generate_dungeon(map_width=map_width,
    #                                       map_height=map_height,
    #                                       engine=self.engine,
    #                                       tile_set=tile_set)
    from ships import HallShip, SphereStarShip
    ship_class = random.choice((HallShip, SphereStarShip))
    ship = ship_class(tile_set.copy())
    #import pdb; pdb.set_trace()
    from procgen_ship import generate_dungeon
    self.engine.game_map = generate_dungeon(self.engine, ship)
    return

    #from procgen import generate_dungeon

    #self.engine.game_map = generate_dungeon(
    #  max_rooms=self.max_rooms,
    #  room_min_size=self.room_min_size,
    #  room_max_size=self.room_max_size,
    #  map_width=self.map_width,
    #  map_height=self.map_height,
    #  engine=self.engine,
    #  tile_set=tile_types.basic_tile_set
    #)
