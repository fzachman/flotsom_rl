import random
import tcod
import numpy as np
import json

import entity_factories
from game_map import GameMap
import tile_types
from wfc import get_wfc, Tile, get_tile_sides
from brushes import load_brushes
from rooms import Room

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
  0: [(entity_factories.stimpack, 35),(entity_factories.energy_cell, 10)],
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
    x,y = random.choice(list(room.coords))

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

def create_path_between(dungeon, tile_set, src_x, src_y, dest_x, dest_y):
  """ This will build an array where every tile that's walkable or a door
      (open doors are walkable but closed doors aren't) is a cost of 1,
      and all walls are 999.  Pathfinding will avoid walls as long as possible,
      until the cost to go through a wall are so high it has no choice.
      Then we'll use that path to find any walls and build traversable spaces."""
  tile_classes = np.array(dungeon.tiles['tile_class'])
  space_weight = np.full((dungeon.width, dungeon.height), fill_value=999, dtype=int)
  cost = np.select([tile_classes=='door', tile_classes=='floor',tile_classes=='space'],
                   [np.ones((dungeon.width,dungeon.height),dtype=int),np.ones((dungeon.width,dungeon.height),dtype=int),space_weight],
                   default=500)


  graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=0)
  pathfinder = tcod.path.Pathfinder(graph)
  pathfinder.add_root((src_x, src_y)) # Start position
  # We'll return every room we traverse through so we can ignore them in future
  # pathing calls.  We'll also suck in all connected rooms
  pathed_to = set([dungeon.room_lookup[(src_x, src_y)]])
  # Compute a path to the destination
  path = pathfinder.path_to((dest_x, dest_y)).tolist()
  path = [(index[0], index[1]) for index in path]
  #print(path)
  last_room = None
  new_tunnel = []
  for i in range(len(path)):
    x, y = path[i]
    path_room = dungeon.room_lookup.get((x,y))
    if path_room:
      last_room = path_room

    if path_room and path_room not in pathed_to:
      connected_rooms = path_room.get_all_connections()
      pathed_to.update(connected_rooms)
    elif dungeon.tiles[x,y]['tile_class'] == 'wall': # If this isn't a room, check to see if it's a wall
      # First check to see if this is just a 1 tile wide wall
      previous_xy = path[i-1]
      source_room = dungeon.room_lookup.get(previous_xy)
      next_xy = path[i+1]
      next_room = dungeon.room_lookup.get(next_xy)
      if source_room is not None and next_room is not None:
        # Simple, add a door between them and connect them.
        #print(f'Adding simple door at ({x},{y})')
        dungeon.tiles[x,y] = tile_set.get_tile_type('door')
        source_room.exits.add((x,y))
        next_room.exits.add((x,y))
        source_room.connect_if_able(next_room)
      else:
        # OK, deal with a longer tunnel.
        if source_room:
          # We're just starting our new tunnel
          new_tunnel = [(x,y)]
        elif next_room:
          # This is the end of the tunnel
          # First add the door at the start of the tunnel and add it to the
          # last rooms exit
          #print(f'Processing tunnel {new_tunnel} that ends at ({x},{y})')
          new_tunnel.reverse()
          try:
            first_exit_x, first_exit_y = new_tunnel.pop()
          except IndexError:
            print(f'Popped from empty list at ({x},{y})')
            continue
          #print(f'Placing starting door at ({first_exit_x}, {first_exit_y})')
          dungeon.tiles[first_exit_x, first_exit_y] = tile_set.get_tile_type('door')
          last_room.exits.add((first_exit_x, first_exit_y))
          if len(new_tunnel) == 0:
            #print(f'Short tunnel detected near ({first_exit_x},{first_exit_y})')
            # We are only a 2 long "tunnel" one of which is now a door, so just add ourselves
            # to the next room and connect the two rooms
            dungeon.tiles[x,y] = tile_set.get_tile_type('floor','basic')
            next_room.exits.add((first_exit_x, first_exit_y))
            next_room.coords.add((x,y))
            next_room.connect_if_able(last_room)
          else:
            # Create an actual tunnel
            # Add this tile as an exit to the next room
            #print(f'Placing ending door at ({x}, {y})')
            dungeon.tiles[x,y] = tile_set.get_tile_type('door')
            next_room.exits.add((x,y))

            for t_x,t_y in new_tunnel:
              dungeon.tiles[t_x,t_y] = tile_set.get_tile_type('floor','basic')

            processed, walls, exits = flood_room(dungeon.tiles, previous_xy[0], previous_xy[1], tile_classes=['floor'])
            new_room = Room(processed, walls, exits)
            new_room.connect_if_able(last_room)
            new_room.connect_if_able(next_room)
            pathed_to.add(new_room)
            dungeon.add_room(new_room)


        else:
          new_tunnel.append((x,y))

  return pathed_to


def generate_dungeon(engine,
                     ship):
  player = engine.player

  dungeon = GameMap(engine, ship.width, ship.height, ship.tile_set, entities=[player])
  print(f'Dungeon size: ({len(dungeon.tiles)}, {len(dungeon.tiles[0])})')

  ship.pre_gen(dungeon.tiles)

  for sector in ship.sectors:
    brush_set = sector.brush_set
    tile_set  = sector.tile_set

    tiles = []
    for b in brush_set.list_brushes():
      brush = b['brush']
      weight = b['weight']
      for data in brush.get_all_rotations():
        sides = get_tile_sides(data, brush.size)
        #print(data, sides)
        tiles.append(Tile(data,sides,weight))

    sector_x1, sector_y1 = sector.x, sector.y
    sector_x2, sector_y2 = sector.x + sector.width - 1, sector.y + sector.height -1
    offset_x, offset_y = sector_x1, sector_y1
    width = sector.width
    height = sector.height

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
  num_holes = random.randint(0,4)
  #print(f'Adding {num_holes} holes')
  for i in range(num_holes):
    x = random.randint(0, ship.width -1)
    y = random.randint(0, ship.height -1)
    if not ship.is_protected(x, y):
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
             0 <= t_x < ship.width and 0 <= t_y < ship.height:
            #print(f'Adding ({t_x},{t_y}) to unprocessed')
            unprocessed.add((t_x, t_y))


  ship.post_gen(dungeon.tiles)

  # Break the map up into rooms
  rooms = find_rooms(dungeon.tiles)
  print(f'Found {len(rooms)} rooms!')
  delete_rooms = []
  for room in rooms:
    if False:#(room.width == 1 or room.height == 1 or len(room.coords) <= 8) and len(room.exits) == 0:
      # Delete this room
      for x,y in room.coords:
        dungeon.tiles[x,y] = tile_set.get_tile_type('wall','basic')
      delete_rooms.append(room)
      #room.color = (0,0,0)
    else:
      for x,y in room.coords:
        if tile_set.is_tile_class(dungeon.tiles[x,y], 'space'):
          room.is_vacuum_source = True
          break
  for room in delete_rooms:
    rooms.remove(room)

  dungeon.rooms = rooms

  # Let's connect some rooms!
  for room in rooms:
    #print('Checking room for exits....')
    num_exits = len(room.exits)
    if num_exits <= 1:
      walls = list(room.walls)
      random.shuffle(walls)
      # If a room has an exits, add between 0 and 1 more
      # If a room has no exits, add between 1 and 2
      exits_needed = random.randint(1 - num_exits,2 - num_exits)
      exits_added = 0
      for wall in walls:
        wall_x, wall_y = wall
        # Certain ship plans set aside pregen areas, so don't touch them
        if not ship.is_protected(wall_x, wall_y):
          # Try not to place 2 doors next to each other.
          is_door_adjacent = False
          for door_x,door_y in ((1,0),(-1,0),(0,1),(0,-1)):
            try:
              if dungeon.tiles[wall_x+door_x,wall_y+door_y]['tile_class'] == 'door':
                is_door_adjacent = True
                break
            except IndexError:
              pass
          if is_door_adjacent:
            print('Skipping wall segment next to a door.')
            continue

          for d_x,d_y in ((1,0),(-1,0),(0,1),(0,-1)):
            t_x = wall_x + d_x
            t_y = wall_y + d_y# Prevent two doors next to each other

            other_room = dungeon.room_lookup.get((t_x, t_y))

            print(f'Checking other room at ({t_x},{t_y}) which is a {other_room} and is self? {other_room == room}')
            if other_room is not None and other_room != room:
              #print('Creating exit!')
              dungeon.tiles[wall_x,wall_y] = tile_set.get_tile_type('door', 'closed')
              room.exits.add(wall)
              #print(f'Walls: {room.walls}, wall: {wall})')
              try:
                room.walls.remove(wall)
              except KeyError:
                pass
              other_room.exits.add(wall)
              try:
                other_room.walls.remove(wall)
              except KeyError:
                pass
              room.connect_if_able(other_room)
              exits_added += 1
            if exits_added >= exits_needed :
              break
          if exits_added >= exits_needed :
            break

  # Don't spawn in a vacuum or start the stairs in one
  # We may want to only start in a clean room to start, then
  # always start in a breached room as we crash into the new ship?
  clean_room_list = []
  for r in list(rooms):
    if not r.is_vacuum_source:
      clean_room_list.append(r)
  random.shuffle(clean_room_list)
  fourths = len(clean_room_list) // 4
  starting_room = random.choice(clean_room_list[:fourths])
  starting_x, starting_y = random.choice(list(starting_room.coords))
  player.place(starting_x,starting_y,dungeon)
  for exit_x, exit_y in starting_room.exits:
    # Close all the doors
    dungeon.tiles[exit_x, exit_y] = tile_set.get_tile_type('door', 'closed')

  end_room = random.choice(clean_room_list[fourths * 3:])
  end_x, end_y = random.choice(list(end_room.coords))
  dungeon.tiles[end_x,end_y] = tile_set.get_tile_type('interactable', 'exit')
  dungeon.downstairs_location = (end_x,end_y)



  pathed_to = set([starting_room])
  for room in rooms:
    #print(f'{len(pathed_to)} rooms checked.')
    if room not in pathed_to:
      dest_x, dest_y = random.choice(list(room.coords))
      pathed_to.update(create_path_between(dungeon, tile_set, starting_x, starting_y, dest_x, dest_y))

  for room in list(rooms):
    place_entities(room, dungeon, engine.game_world.current_floor)

  return dungeon
