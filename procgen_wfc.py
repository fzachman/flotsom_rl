import random
import tcod
import numpy as np
import json

import entity_factories
from game_map import GameMap
import tile_types
from wfc import get_wfc, Tile, get_tile_sides
from brushes import Brush, BrushSet

max_items_by_floor = [
 (1,1),
 (4,2),
]

max_monsters_by_floor = [
 (1,2),
 (4,3),
 (6,5)
]

item_chances = {
  0: [(entity_factories.stimpack, 35),(entity_factories.power_fist, 105),(entity_factories.energy_cell, 105)],
  2: [(entity_factories.neural_scrambler, 10),],
  4: [(entity_factories.laser_drone, 25),(entity_factories.power_fist, 5)],
  6: [(entity_factories.grenade_fire, 25),(entity_factories.armored_spacer_suit, 15)],
}

enemy_chances = {
  0: [(entity_factories.crazed_crewmate, 80)],
  3: [(entity_factories.xeno_scuttler, 15)],
  5: [(entity_factories.xeno_scuttler, 30)],
  7: [(entity_factories.xeno_scuttler, 60)],
}

# Technically, numpy is storing our data sideways, where
# x is height and y is width, but since we always access it as
# x = width and y = height, it gets rendered that way so we
# will just keep pretending x = width
cardinal_directions = {
  'up': (0,-1),
  'down': (0,1),
  'left': (-1,0),
  'right': (1,0)
}

diagonal_directions = {
  'up_left': (-1,-1),
  'up_right': (1,-1),
  'down_left': (-1,1),
  'down_right': (1,1)
}

all_directions = list(cardinal_directions.values()) + list(diagonal_directions.values())
card_directions = ((0,-1), (0,1), (-1,0), (1,0))

def get_max_value_for_floor(max_value_by_floor, floor):
  current_value = 0
  for floor_minimum, value in max_value_by_floor:
    if floor_minimum > floor:
      break
    else:
      current_value = value
  return current_value

def get_entities_at_random(weighted_chances_by_floor, number_of_entities, floor):
  entity_weighted_chances = {}
  for key, values in weighted_chances_by_floor.items():
    if key > floor:
      break
    else:
      for value in values:
        entity = value[0]
        weighted_chance = value[1]
        entity_weighted_chances[entity] = weighted_chance

  entities = list(entity_weighted_chances.keys())
  entity_weighted_chance_values = list(entity_weighted_chances.values())

  chosen_entities = random.choices(
    entities, weights=entity_weighted_chance_values, k=number_of_entities
  )

  return chosen_entities



def place_entities(room, dungeon, floor_number):
  number_of_monsters = random.randint(0, get_max_value_for_floor(max_monsters_by_floor, floor_number))
  number_of_items = random.randint(0, get_max_value_for_floor(max_items_by_floor, floor_number))

  monsters = get_entities_at_random(enemy_chances, number_of_monsters, floor_number)
  items = get_entities_at_random(item_chances, number_of_items, floor_number)

  for entity in monsters + items:
    x = random.randint(room.x1 + 1, room.x2 - 1)
    y = random.randint(room.y1 + 1, room.y2 - 1)

    if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
      entity.spawn(dungeon, x, y)

def tunnel_between(start, end):
  """ Return an L-shaped tunnel between these two points (x,y) """
  x1, y1 = start
  x2, y2 = end
  if random.random() < 0.5:  # 50% chance.
    # Move horizontally, then vertically.
    corner_x, corner_y = x2, y1
  else:
    # Move vertically, then horizontally.
    corner_x, corner_y = x1, y2

  # Generate the coordinates for this tunnel.
  for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
    yield x, y
  for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
    yield x, y

def subdivide(x, y, width, height, num_times):
  """Assuming x,y/w,h is a box, recursively divide it into
  smaller boxes of semi-random size and return the corners of each
  box.  Yes, this code could probably be optimized."""
  divisions = []
  if width > height:
    x1a = x
    x_third = (width-1) // 3
    x1b = x1a + random.randint(x_third, x_third*2)
    y1a = y
    y1b = y + height - 1

    x2a = x1b + 1
    x2b = x + width - 1
    y2a = y1a
    y2b = y1b

  else:
    y_third = (height-1) // 3
    x1a = x
    x1b = x + width - 1
    y1a = y
    y1b = y1a + random.randint(y_third, y_third*2)

    x2a = x1a
    x2b = x1b
    y2a = y1b + 1
    y2b = y + height - 1

  side1 = ((x1a,y1a),(x1b,y1b))
  side2 = ((x2a,y2a),(x2b,y2b))
  num_times -= 1
  if num_times > 0:
    for side in (side1, side2):
      s_x = side[0][0]
      s_y = side[0][1]
      s_width = side[1][0] - s_x + 1
      s_height = side[1][1] - s_y + 1
      divisions.extend(subdivide(s_x, s_y, s_width, s_height, num_times))
  else:
    divisions.extend([side1, side2])
  return divisions

class Room:
  def __init__(self, coords, walls, exits):
    self.coords = coords # Basically walkable tiles in this room, floors and space usually
    self.walls = walls # Usefull if we have no exits to find a wall to place a door
    self.min_x = 9999
    self.max_x = 0
    self.min_y = 9999
    self.max_y = 0
    for x, y in coords:
      if x < self.min_x:
        self.min_x = x
      if x > self.max_x:
        self.max_x = x
      if y < self.min_y:
        self.min_y = y
      if y > self.max_y:
        self.max_y = y

    self.exits = exits
    removed = set()
    for x,y in self.exits:
      if ((x+1,y) in self.coords and (x-1,y) in self.coords) or \
         ((x,y-1) in self.coords and (x,y+1) in self.coords):
        # If both tiles along one axis are part of this room, this is
        # an internally connected door that doesn't lead to another room,
        # so remove it as an exit.
        removed.add((x,y))
    self.exits.difference_update(removed)

    self.connecting_rooms = set()
    self.color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))

  @property
  def width(self):
    return self.max_x - self.min_x + 1

  @property
  def height(self):
    return self.max_y - self.min_y + 1

  def connect_if_able(self, other_room):
    if len(self.exits.intersection(other_room.exits)) > 0:
      self.connecting_rooms.add(other_room)
      other_room.connecting_rooms.add(self)

  def intersects(self, other_room):
    if self.tiles.intersection(other_room.tiles):
      return True
    else:
      return False



def find_rooms(tiles):
  processed = set()
  rooms = []
  for x in range(len(tiles)):
    for y in range(len(tiles[0])):
      coord = (x,y)
      if coord not in processed:
        processed.add(coord)
        if tiles[x,y]['tile_class'] in ('floor', 'space'):
          room_coords, wall_coords, exit_coords = flood_room(tiles, x, y)
          room = Room(room_coords, wall_coords, exit_coords)
          rooms.append(room)
          processed.update(room_coords)
          processed.update(exit_coords)
          processed.update(wall_coords)
  for i, room1 in enumerate(rooms,start=1):
    for room2 in rooms[i:]:
      room1.connect_if_able(room2)
  return rooms

def flood_room(tiles, x, y,processed=None, tile_classes=['floor','space']):
  if not processed:
    processed = set()
  walls = set()
  exits = set()
  processed.add((x,y))
  for d_x,d_y in card_directions:
    t_x = x + d_x
    t_y = y + d_y
    if (t_x, t_y) not in processed:
      try:
        if tiles[t_x,t_y]['tile_class'] in tile_classes:
          new_processed, new_walls, new_exits = flood_room(tiles, t_x,t_y, processed, tile_classes)
          processed.update(new_processed)
          exits.update(new_exits)
          walls.update(new_walls)
        elif tiles[t_x,t_y]['tile_class'] == 'door':
          exits.add((t_x,t_y))
        elif tiles[t_x,t_y]['tile_class'] == 'wall':
          walls.add((t_x,t_y))
      except IndexError:
        # Cheaper to do this when nearing an edge than doing an if check every loop
        pass
  return processed, walls, exits



def generate_dungeon(map_width,
                     map_height,
                     engine,
                     tile_set):
  player = engine.player

  dungeon = GameMap(engine, map_width, map_height, tile_set, entities=[player])
  print(f'Dungeon size: ({len(dungeon.tiles)}, {len(dungeon.tiles[0])})')

  ##################################
  # LOAD BRUSHES, PAINT THE WORLD! #
  ##################################
  # If we're sticking with WFC, should this be in game_map.GameWorld?
  brushes = {}
  brush_sets = {}
  with open('brushes.json', 'r') as f:
    brush_data = json.loads(f.read())
    for b in brush_data['brushes']:
      brush = Brush(b['name'],b['size'],b['data'])
      brushes[brush.name] = brush
    for s in brush_data['brush_sets']:
      brush_set = BrushSet(s['name'], s['brush_size'])
      for b in s['brushes']:
        brush = brushes.get(b['brush_name'])
        if brush:
          weight = b['weight']
          brush_set.add_brush(brush, weight)
      brush_sets[brush_set.name] = brush_set

  # TODO: Move this code down into the loop to pull different looks per sector
  # should also have some sort of "ship type" object that stores available brush
  # sets.


  # Subdivide our map into different sectors so we can populate each
  # one with its own brush set/style.  Buffer 5 spaces around the map
  # for SPAAAAAAAAAAAAAAAAAAAAAAAAAAACE.
  sectors = subdivide(5,5, map_width - 10, map_height - 10, 2)
  for sector in sectors:#offset_x, offset_y in ((0,0), (map_width // 2 -1,0), (0, map_height // 2 -1), (map_width // 2-1, map_height // 2-1)):
    # The corner of the main map to insert our generated data in, ie. our sector
    brush_set = random.choice(list(brush_sets.values()))#['round']
    tiles = []
    for b in brush_set.list_brushes():
      brush = b['brush']
      weight = b['weight']
      for data in brush.get_all_rotations():
        sides = get_tile_sides(data, brush.size)
        #print(data, sides)
        tiles.append(Tile(data,sides,weight))

    sector_x1, sector_y1 = sector[0]
    sector_x2, sector_y2 = sector[1]
    offset_x, offset_y = sector_x1, sector_y1
    width = sector_x2 - sector_x1 + 1
    height = sector_y2 - sector_y1 + 1

    tile_size = brush_set.brush_size
    plan_width = width // (tile_size)
    plan_height = height // (tile_size)
    tile_plan = np.array(get_wfc(tiles=tiles, tile_size=tile_size, width=plan_width, height=plan_height))
    #print(tile_plan)
    print(f'Plan: ({plan_width}, {plan_height}), Rendered plan:  ({len(tile_plan[0])} {len(tile_plan)}), Sector: ({sector_x1},{sector_y1})({width},{height})')
    #print(f'Map: ({map_width},{map_height}), Actual Map: ({len(dungeon.tiles)},{len(dungeon.tiles[0])})')
    rendered_width = len(tile_plan)
    rendered_height = len(tile_plan[0])

    for x in range(rendered_width):
      tile_plan[x,0] = 0
      tile_plan[x, rendered_height - 1] = 0
    for y in range(rendered_height):
      tile_plan[0,y] = 0
      tile_plan[rendered_width - 1, y] = 0

    for x in range(rendered_width):
      for y in range(rendered_height):
        if 0 < x < rendered_width-1 and 0 < y < rendered_height-1 and tile_plan[x,y] == 255:
          #print(f'({x},{y})')
          # Check to see if this should be a doorway:
          if tile_plan[x-1,y] == 0 and tile_plan[x+1,y] == 0 and \
             tile_plan[x,y-1] == 255 and tile_plan[x,y+1] == 255:
            # possible vertical door.  Make sure at least one side
            # has open space so we're not filling hallways with doors
            if tile_plan[x-1,y-1] == 255 or tile_plan[x+1,y-1] == 255 or \
               tile_plan[x+1,y+1] == 255 or tile_plan[x+1,y+1] == 255:
              try:
                if tile_plan[x, y+2] == 0 or tile_plan[x,y-2] == 0:
                  # If there's a wall right after the floor, assume we're in a turning
                  # hallway or some other narrow space that doesn't need a door
                  continue
                else:
                  # Flag this is a vertical door
                  tile_plan[x,y] = 3
              except IndexError:
                # If we're that close to the edge, don't bother with a door.
                pass
          elif tile_plan[x,y-1] == 0 and tile_plan[x,y+1] == 0 and \
               tile_plan[x-1,y] == 255 and tile_plan[x+1,y] == 255:
            # Possible horizontal door
            if tile_plan[x-1,y-1] == 255 or tile_plan[x+1,y-1] == 255 or \
               tile_plan[x+1,y+1] == 255 or tile_plan[x+1,y+1] == 255:
              try:
                if tile_plan[x+2,y] == 0 or tile_plan[x-2,y] == 0:
                  continue
                else:
                  # Flag this is a horizontal door
                  tile_plan[x,y] = 3
              except IndexError:
                pass

    #print('\n'.join([''.join(str(c) for c in r) for r in tile_plan.tolist()]))
    for x in range(0,rendered_height):
      for y in range(0,rendered_width):
        #print(f'({x},{y}), plan:  ({len(tile_plan[0])} {len(tile_plan)}), Map: ({map_width},{map_height})')
        plan_type = tile_plan[y,x]
        map_x = x + offset_x#* 3
        map_y = y + offset_y#* 3
        #print(f'pulling {plan_type} from ({x},{y}), placing in map at ({map_x},{map_y})')
        if plan_type == -1:
          dungeon.tiles[map_x, map_y] = tile_set.get_tile_type('space', 'basic')
        if plan_type == 0:
          dungeon.tiles[map_x,map_y] = tile_set.get_tile_type('wall', 'basic')
        elif plan_type == 255:
          dungeon.tiles[map_x,map_y] = tile_set.get_tile_type('floor', 'basic')
        elif plan_type == 3:
          dungeon.tiles[map_x,map_y] = tile_set.get_tile_type('door')



  # Punch some holes and make some SPAAAAAAAAAAAAAAAAAAAAAAAAAAACE #
  num_holes = random.randint(0,6)
  #print(f'Adding {num_holes} holes')
  for i in range(num_holes):
    x = random.randint(0, map_width -1)
    y = random.randint(0, map_height -1)
    dungeon.tiles[x,y] = tile_set.get_tile_type('space','basic')
    max_hole_size = random.randint(20,80)
    hole_tiles = set([(x,y)])
    unprocessed = set()
    for d_x, d_y in [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(-1,1),(-1,1),(1,1)]:
      # Add the tiles around so we always have a starting position
      unprocessed.add((x+d_x, y+d_y))
    while len(hole_tiles) < max_hole_size:
      if len(unprocessed) == 0:
        break
      x,y = here = unprocessed.pop()

      try:
        dungeon.tiles[x, y] = tile_set.get_tile_type('space','basic')
      except IndexError:
        continue
      hole_tiles.add(here)
      # Pick a random direction
      for j in range(random.randint(1,4)):
        d_x, d_y = random.choice([(0,-1),(0,1),(-1,0),(1,0)])
        t_x = x + d_x
        t_y = y + d_y
        if (t_x,t_y) not in hole_tiles and (t_x,t_y) not in unprocessed and \
           0 <= t_x < map_width and 0 <= t_y < map_height:
          #print(f'Adding ({t_x},{t_y}) to unprocessed')
          unprocessed.add((t_x, t_y))

  # Break the map up into rooms
  rooms = find_rooms(dungeon.tiles)
  print(f'Found {len(rooms)} rooms!')
  delete_rooms = []
  for room in rooms:
    if (room.width == 1 or room.height == 1) and len(room.exits) == 0:
      # Delete this room
      for x,y in room.coords:
        dungeon.tiles[x,y] = tile_set.get_tile_type('wall','basic')
      delete_rooms.append(room)
      #room.color = (0,0,0)
  for room in delete_rooms:
    rooms.remove(room)

  dungeon.rooms = rooms

  # Let's just see what that looks like
  # Pick a corner for the player to start in
  # This is ugly and should probably be optimized.  Maybe by sector.
  corner = random.randint(1,4)
  if corner == 1:
    # start in upper left/(0,0):
    x_range = range(0, map_width // 2)
    y_range = range(0, map_height // 2)
    exit_x_range = range(map_width - 1, map_width // 2, -1)
    exit_y_range = range(map_height - 1, map_height // 2, -1)
  elif corner == 2:
    # upper right
    x_range = range(map_width - 1, map_width // 2, -1)
    y_range = range(0, map_height // 2)
    exit_x_range = range(0, map_width // 2)
    exit_y_range = range(map_height - 1, map_height // 2, -1)
  elif corner == 3:
    # lower right
    x_range = range(map_width - 1, map_width // 2, -1)
    y_range = range(map_height - 1, map_height // 2, -1)
    exit_x_range = range(0, map_width // 2)
    exit_y_range = range(0, map_height // 2)
  else:
    # lower left!
    x_range = range(0, map_width // 2)
    y_range = range(map_height - 1, map_height // 2, -1)
    exit_x_range = range(map_width - 1, map_width // 2, -1)
    exit_y_range = range(0, map_height // 2)


  player_placed = False
  while not player_placed:
    x = random.choice(x_range)
    y = random.choice(y_range)
    if tile_set.is_tile_class(dungeon.tiles[x,y], 'floor'):
      player.place(x,y,dungeon)
      player_placed = True

  exit_placed = False
  while not exit_placed:
    x = random.choice(exit_x_range)
    y = random.choice(exit_y_range)
    if tile_set.is_tile_class(dungeon.tiles[x,y], 'floor'):
      dungeon.tiles[x,y] = tile_set.get_tile_type('interactable', 'exit')#tile_types.down_stairs
      dungeon.downstairs_location = (x,y)
      exit_placed = True

  return dungeon
