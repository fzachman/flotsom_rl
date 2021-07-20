import random
import tcod
import numpy as np

import entity_factories
from game_map import GameMap
import tile_types
from wfc import get_wfc, Tile

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

class RectangularRoom:
  def __init__(self, x, y, width, height):
    self.x1 = x
    self.y1 = y
    self.x2 = x + width
    self.y2 = y + height

  @property
  def center(self):
    center_x = int((self.x1 + self.x2) / 2)
    center_y = int((self.y1 + self.y2) / 2)

    return center_x, center_y

  @property
  def inner(self):
    """Return the inner area of this room as a 2D array index."""
    return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

  def intersects(self, other):
    """ Return True if this room overlaps with another RectangularRoom"""
    return (self.x1 <= other.x2 and
            self.x2 >= other.x1 and
            self.y1 <= other.y2 and
            self.y2 >= other.y1)


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


def generate_dungeon(map_width,
                     map_height,
                     engine,
                     tile_set):
  player = engine.player

  dungeon = GameMap(engine, map_width, map_height, tile_set, entities=[player])
  print(f'Dungeon size: ({len(dungeon.tiles)}, {len(dungeon.tiles[0])})')
  source = np.array([[0,0,0,0,0,0,0,0,0,0],
            [0,0,1,1,1,1,1,1,0,1],
            [0,0,1,1,1,1,1,1,0,1],
            [0,1,1,1,1,1,1,1,0,1],
            [0,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,0,1],
            [0,1,1,1,1,1,1,1,0,1],
            [0,1,1,1,1,1,1,1,0,1],
            [0,1,1,1,1,1,1,1,0,1],
            [0,0,0,0,0,0,0,0,0,0],
  ])
  source2 = np.array([[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
                      [2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,2,2],
                      [2,2,2,2,2,2,2,0,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,2,2,2,2,2,0,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,2,2,2,2,2,0,0,0,0,1,1,1,1,1,1,0,2,2],
                      [2,2,2,2,2,2,2,2,2,2,0,0,0,1,0,0,0,0,2,2],
                      [2,2,0,0,0,0,0,0,2,2,2,2,0,1,0,1,2,2,2,2],
                      [2,2,0,1,1,1,1,0,2,2,2,2,0,1,0,1,2,2,2,2],
                      [2,2,0,1,1,1,1,0,0,0,0,0,0,1,0,1,2,2,2,2],
                      [2,2,0,1,1,1,1,1,1,1,1,1,1,1,0,1,2,2,2,2],
                      [2,2,0,1,1,1,1,0,0,0,0,0,0,0,0,1,2,2,2,2],
                      [2,2,0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2],
  ])

  source3 = np.array([[2,2,2,2,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0,2],
                      [2,2,2,0,0,1,1,1,0,0,2,2,2,2,0,1,1,1,0,2],
                      [2,2,0,0,1,1,1,1,1,0,0,2,2,2,0,1,1,1,0,2],
                      [2,0,0,1,1,1,1,1,1,1,0,0,2,2,0,0,1,0,0,2],
                      [0,0,1,1,1,1,1,1,1,1,1,0,0,2,2,0,1,0,2,2],
                      [0,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,0,2,2],
                      [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [0,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,0,2,2],
                      [0,0,1,1,1,1,1,1,1,1,1,0,0,2,2,0,1,0,2,2],
                      [2,0,0,1,1,1,1,1,1,1,0,0,2,2,2,0,1,0,2,2],
                      [2,2,0,0,1,1,1,1,1,0,0,2,2,2,2,0,1,0,2,2],
                      [2,2,2,0,0,1,1,1,0,0,2,2,2,2,2,0,1,0,2,2],
                      [2,2,2,2,0,0,0,0,0,2,2,2,2,2,2,0,1,0,2,2],
                      [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,1,0,2,2],
                      [2,2,2,2,0,0,0,0,0,0,0,0,0,2,2,0,1,0,2,2],
                      [2,2,2,0,0,1,1,1,1,1,1,1,0,0,0,0,1,0,2,2],
                      [2,2,2,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,2,2],
                      [2,2,2,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,2,2],
                      [2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2],
                      [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],])




  # 0's are walls, 1's are floors
  tile_size = 5
  plan_width = map_width // 2 // tile_size
  plan_height = map_height // 2 // tile_size
  for offset_x, offset_y in ((0,0), (map_width // 2 -1,0), (0, map_height // 2 -1), (map_width // 2-1, map_height // 2-1)):
    source = random.choice([source2,source3])
    #tile_plan = np.array(get_tiles((len(source),len(source[0])), (plan_width, plan_height), source, sample_size=2, debug=False))
    tile_plan = np.array(get_wfc(source3, tile_size=tile_size, width=plan_width, height=plan_height))
    #print(tile_plan)
    print(f'Plan: ({plan_width}, {plan_height}), Rendered plan:  ({len(tile_plan[0])} {len(tile_plan)})')
    print(f'Map: ({map_width},{map_height}), Actual Map: ({len(dungeon.tiles)},{len(dungeon.tiles[0])})')
    rendered_width = len(tile_plan)
    rendered_height = len(tile_plan[0])
    for x in range(rendered_width):
      for y in range(rendered_height):
        if x == 0 or y == 0 or x == rendered_width -1 or y == rendered_height - 1:
          # Seal the edges of the map:
          #pass
          tile_plan[x,y] = 0
        elif 0 < x < rendered_width-2 and 0 < y < rendered_height-2 and tile_plan[x,y] == 1:
          #print(f'({x},{y})')
          # Check to see if this should be a doorway:
          if tile_plan[x-1,y] == 0 and tile_plan[x+1,y] == 0 and \
             tile_plan[x,y-1] == 1 and tile_plan[x,y+1] == 1:
            # possible vertical door.  Make sure at least one side
            # has open space so we're not filling hallways with doors
            if tile_plan[x-1,y-1] == 1 or tile_plan[x+1,y-1] == 1 or \
               tile_plan[x+1,y+1] == 1 or tile_plan[x+1,y+1] == 1:
              # Flag this is a vertical door
              tile_plan[x,y] = 3
          elif tile_plan[x,y-1] == 0 and tile_plan[x,y+1] == 0 and \
               tile_plan[x-1,y] == 1 and tile_plan[x+1,y] == 1:
            # Possible horizontal door
            if tile_plan[x-1,y-1] == 1 or tile_plan[x+1,y-1] == 1 or \
               tile_plan[x+1,y+1] == 1 or tile_plan[x+1,y+1] == 1:
              # Flag this is a horizontal door
              tile_plan[x,y] = 3

    #print('\n'.join([''.join(str(c) for c in r) for r in tile_plan.tolist()]))
    for x in range(0,rendered_height):
      for y in range(0,rendered_width):
        #print(f'({x},{y}), plan:  ({len(tile_plan[0])} {len(tile_plan)}), Map: ({map_width},{map_height})')
        plan_type = tile_plan[y,x]
        map_x = x + offset_x#* 3
        map_y = y + offset_y#* 3
        #print(f'pulling {plan_type} from ({x},{y}), placing in map at ({map_x},{map_y})')
        if plan_type in (0,2):
          #dungeon.tiles[map_x:map_x+3,map_y:map_y+3] = np.full((3,3), fill_value=tile_set.get_tile_type('wall', 'basic'))
          dungeon.tiles[map_x,map_y] = tile_set.get_tile_type('wall', 'basic')
        elif plan_type == 1:
          #dungeon.tiles[map_x:map_x+3,map_y:map_y+3] = np.full((3,3), fill_value=tile_set.get_tile_type('floor', 'basic'))
          dungeon.tiles[map_x,map_y] = tile_set.get_tile_type('floor', 'basic')
        elif plan_type == 3:
          # Vertical door
          #brush = np.full((3,3), fill_value=tile_set.get_tile_type('wall', 'basic'))
          #brush[1,0] = tile_set.get_tile_type('floor', 'basic')
          #brush[1,2] = tile_set.get_tile_type('floor', 'basic')
          #brush[1,1] = tile_set.get_tile_type('door')
          #dungeon.tiles[map_x:map_x+3,map_y:map_y+3] = brush[0:3,0:3]
          dungeon.tiles[map_x,map_y] = tile_set.get_tile_type('door')
        elif plan_type == 99:
          # horizontal door
          brush = np.full((3,3), fill_value=tile_set.get_tile_type('wall', 'basic'))
          brush[0,1] = tile_set.get_tile_type('floor', 'basic')
          brush[2,1] = tile_set.get_tile_type('floor', 'basic')
          brush[1,1] = tile_set.get_tile_type('door')
          #dungeon.tiles[map_x:map_x+3,map_y:map_y+3] = brush[0:3,0:3]
          dungeon.tiles[map_x,map_y] = tile_set.get_tile_type('door')

  # Let's just see what that looks like
  # Pick a corner for the player to start in
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
  for x in x_range:
    for y in y_range:
      #print(f'Checking if ({x},{y}) is a floor.  It is a {dungeon.tiles[x,y]}')
      if tile_set.is_tile_class(dungeon.tiles[x,y], 'floor'):
        #print(f'Placing player at ({x},{y})')
        player.place(x,y, dungeon)
        player_placed = True
        break
    if player_placed:
      break

  exit_placed = False
  for x in exit_x_range:
    for y in exit_y_range:
      if tile_set.is_tile_class(dungeon.tiles[x,y], 'floor'):
        #print(f'Placing exit at ({x},{y})')
        dungeon.tiles[x,y] = tile_set.get_tile_type('interactable', 'exit')#tile_types.down_stairs
        dungeon.downstairs_location = (x,y)
        exit_placed = True
        break
    if exit_placed:
      break
  return dungeon

  rooms = []

  center_of_last_room = (0,0)

  for r in range(max_rooms):
    if r == 0:
      # Hack first room for testing
      room_width = 15
      room_height = 15
      x = int(dungeon.width / 2) - 7
      y = int(dungeon.height / 2) - 7
    else:
      room_width = random.randint(room_min_size, room_max_size)
      room_height = random.randint(room_min_size, room_max_size)

      x = random.randint(0, dungeon.width - room_width - 1)
      y = random.randint(0, dungeon.height - room_height - 1)

    # "RectangularRoom" class makes rectangles easier to work with
    new_room = RectangularRoom(x, y, room_width, room_height)

    # Run through the other rooms and see if they intersect with this one.
    if any(new_room.intersects(other_room) for other_room in rooms):
      continue  # This room intersects, so go to the next attempt.
    # If there are no intersections then the room is valid.

    # Dig out this rooms inner area.
    for rx in range(new_room.x1, new_room.x2):
      for ry in range(new_room.y1, new_room.y2):
        dungeon.tiles[rx,ry] = tile_set.get_tile_type('floor', 'basic')
    #dungeon.tiles[new_room.inner] = tile_types.floor_room

    if len(rooms) == 0:
      # The first room, where the player starts.
      player.place(*new_room.center, dungeon)
      # Place all equipment for testing
      entity_factories.knife.spawn(dungeon, new_room.x1+1, new_room.y1+1)
      entity_factories.power_fist.spawn(dungeon, new_room.x1+2, new_room.y1+1)
      entity_factories.popgun.spawn(dungeon, new_room.x1+3, new_room.y1+1)
      entity_factories.spacer_suit.spawn(dungeon, new_room.x1+4, new_room.y1+1)
      entity_factories.armored_spacer_suit.spawn(dungeon, new_room.x1+5, new_room.y1+1)
      entity_factories.stimpack.spawn(dungeon, new_room.x1+1, new_room.y1+2)
      entity_factories.neural_scrambler.spawn(dungeon, new_room.x1+2, new_room.y1+2)
      entity_factories.grenade_fire.spawn(dungeon, new_room.x1+3, new_room.y1+2)
      entity_factories.laser_drone.spawn(dungeon, new_room.x1+4, new_room.y1+2)
      entity_factories.energy_cell.spawn(dungeon, new_room.x1+1, new_room.y1+3)
      entity_factories.energy_cell.spawn(dungeon, new_room.x1+2, new_room.y1+3)
      entity_factories.energy_cell.spawn(dungeon, new_room.x1+3, new_room.y1+3)
    else:  # All rooms after the first.
      # Dig out a tunnel between this room and the previous one.
      first_wall = None
      last_wall = None
      for x, y in tunnel_between(rooms[-1].center, new_room.center):
        if tile_set.is_tile_class(dungeon.tiles[x,y], 'wall'):# == tile_types.wall:
          if not first_wall:
            first_wall = (x,y)
          else:
            last_wall = (x,y)
          dungeon.tiles[x, y] = tile_set.get_tile_type('floor', 'hall')#tile_types.floor_hall

      if first_wall:# and random.random() <= 0.5:
        dungeon.tiles[first_wall[0],first_wall[1]] = tile_set.get_tile_type('door')#tile_types.door_closed
      if last_wall:# and random.random() <= 0.5:
        dungeon.tiles[last_wall[0],last_wall[1]] = tile_set.get_tile_type('door')#tile_types.door_closed

      center_of_last_room = new_room.center


    place_entities(new_room, dungeon, engine.game_world.current_floor)
    # Finally, append the new room to the list.
    rooms.append(new_room)

  dungeon.tiles[center_of_last_room] = tile_set.get_tile_type('interactable', 'exit')#tile_types.down_stairs
  dungeon.downstairs_location = center_of_last_room


  return dungeon
