import lzma
import pickle
import random
import tcod
import numpy as np

import entity_factories
from game_map import GameMap
import tile_types
from sectors import SectorTemplate, SectorExitMap

"""
Notes:
tile editor, create template of rooms.  Rooms have access point tiles
and hallways connecting the rooms pregenned.  At run time, access point
tiles will be randomly populated with doors (opened/closed) or walls (or
left open) providing dynamic routes through the set of rooms.

Each section will have 3 exit possibilities per side, dividing the entire
section into 9 sub sections.  Generate exits to another section in random
sub sections.  Sub sections without exists have a chance to have a breech,
which would replace another random or templated pattern of tiles with
"space" tiles.

Breeches/low oxygen would spread from space tiles through all possible
pathways.  This means opening a door would temporarily vaccuum more sections
until doors were closed.

Space tiles can have types:
 -open " "
 -big star "*"
 -little star "."
At the end of each round each space tile would copy its pattern from the
space tile to its left.  If the left tile is not a space tile, generate a
new space tile.  This will, hopefully, look like the stars are moving/ship
is rotating.
"""

class Room:
  def __init__(self, tile_coords):
    """ A Class containing all the coordinates of a room """
    self.tile_coords = tile_coords

cardinal_directions = ((0,-1),(0,1),(-1,0),(1,0))
def generate_dungeon(sector_width,
                     sector_height,
                     max_sectors,
                     map_width_in_sectors,
                     map_height_in_sectors,
                     engine):
  player = engine.player
  airlock_length = 3 # How long, in tiles, the airlocks connecting sectors are
  map_width = sector_width * map_width_in_sectors + ((map_width_in_sectors - 1) * airlock_length)
  map_height = sector_height * map_height_in_sectors + ((map_height_in_sectors - 1) * airlock_length)

  dungeon = GameMap(engine, map_width, map_height, entities=[player])

  with open(f'sectors_{sector_width}x{sector_height}.dat', 'rb') as f:
    print('Loading sectors...')
    sector_templates = pickle.loads(lzma.decompress(f.read()))
    print('...loaded %s sectors' % (len(sector_templates)))

  dungeon_rooms = []

  sector_map = []
  for y in range(map_height_in_sectors):
    row = []
    for x in range(map_width_in_sectors):
      row.append(None)
    sector_map.append(row)
  sector_map = np.array(sector_map, SectorExitMap)

  last_sector_xy = None
  for i in range(max_sectors):

    # First completely generate the sector including doors and breaches
    tiles = random.choice(sector_templates).randomize()
    place_interior_exits(tiles)
    # TODO: Place Breaches

    sector_exit_map = SectorExitMap(tiles)
    if not last_sector_xy:
      # This is our first sector, place it randomly on the map
      # Create our sector map so we can join sectors together with airlocks
      sector_x = random.randint(0,2)
      sector_y = random.randint(0,2)
      sector_map[sector_x, sector_y] = sector_exit_map
    else:
      adjacent_sectors = get_adjacent_sectors(sector_x, sector_y, sector_map)
      if adjacent_sectors:
        adjacent_sector = adjacent_sectors[0]
        sector_x = adjacent_sector[0]
        sector_y = adjacent_sector[1]
        sector_map[sector_x, sector_y] = sector_exit_map
      else:
        # If there are no adjacent sectors, we are pretty much done.  We've wormed
        # our way into a corner with no escape!
        break


    # Place our sector tiles in the map position indicated by our sector map
    # spaced out with enough room to put an airlock between them.
    map_x1 = sector_width * sector_x + airlock_length * sector_x
    map_y1 = sector_height * sector_y + airlock_length * sector_y
    map_x2 = map_x1 + sector_width
    map_y2 = map_y1 + sector_height
    dungeon.tiles[map_x1: map_x2, map_y1: map_y2] = tiles

    if last_sector_xy:
      # Connect this sector with the previous one
      # Get the SectorExitMap for the previous tile, get its offset so we can find its position on the
      # real map, then translate all the correct exits to actual map coords.
      last_sector_x, last_sector_y = last_sector_xy
      last_sector_exit_map = sector_map[last_sector_x, last_sector_y]
      last_map_x1 = sector_width * last_sector_x + airlock_length * last_sector_x
      last_map_y1 = sector_height * last_sector_y + airlock_length * last_sector_y

      if last_sector_x == sector_x:
        # Same column, vertical connection
        if last_sector_y < sector_y:
          # We are lower
          exit1_x, exit1_y = random.choice(sector_exit_map.north_exits)
          exit2_x, exit2_y = random.choice(last_sector_exit_map.south_exits)
          print(f'We are lower: Exit1: ({exit1_x},{exit1_y}), Exit2: ({exit2_x},{exit2_y})')
          tunnel = tunnel_between((exit1_x + map_x1, exit1_y + map_y1),
                                  (exit2_x + last_map_x1, exit2_y + last_map_y1),
                                  'v')
        else:
          # We are higher than the last sector
          exit1_x, exit1_y = random.choice(sector_exit_map.south_exits)
          exit2_x, exit2_y = random.choice(last_sector_exit_map.north_exits)
          print(f'We are higher: Exit1: ({exit1_x},{exit1_y}), Exit2: ({exit2_x},{exit2_y})')
          tunnel = tunnel_between((exit1_x + map_x1, exit1_y + map_y1),
                                  (exit2_x + last_map_x1, exit2_y + last_map_y1),
                                  'v')
      else:
        # Same row, horizontal connection
        if last_sector_x < sector_x:
          # We are right of the last sector
          exit1_x, exit1_y = random.choice(sector_exit_map.west_exits)
          exit2_x, exit2_y = random.choice(last_sector_exit_map.east_exits)
          tunnel = tunnel_between((exit1_x + map_x1, exit1_y + map_y1),
                                  (exit2_x + last_map_x1, exit2_y + last_map_y1),
                                  'h')
        else:
          exit1_x, exit1_y = random.choice(sector_exit_map.east_exits)
          exit2_x, exit2_y = random.choice(last_sector_exit_map.west_exits)
          tunnel = tunnel_between((exit1_x + map_x1, exit1_y + map_y1),
                                  (exit2_x + last_map_x1, exit2_y + last_map_y1),
                                  'h')
      for i, location in enumerate(tunnel):
        if i == 0 or i == len(tunnel) - 1:
          # Put a closed door at both ends
          dungeon.tiles[location[0],location[1]] = tile_types.door_closed
        else:
          dungeon.tiles[location[0],location[1]] = tile_types.floor_airlock

    # Generate room data for this sector
    rooms = find_rooms(dungeon, map_x1, map_y1, map_x2, map_y2)
    dungeon_rooms.extend(rooms)

    # If we haven't placed our player yet, find an open floor tile in this sector to place them
    if player.x == 0 and player.y == 0:
      starting_room = random.choice(rooms)
      starting_xy = random.choice(starting_room.tile_coords)
      player.place(starting_xy[0], starting_xy[1], dungeon)


    last_sector_xy = (sector_x, sector_y)

  # Finally, fill all unused sector transition exits with walls.
  for y, row in enumerate(dungeon.tiles):
    for x, tile in enumerate(row):
      if dungeon.tiles[x,y] == tile_types.exit_point:
        dungeon.tiles[x,y] = tile_types.wall

  return dungeon

def get_adjacent_sectors(x, y, sector_map):
  adjacent = []
  for dx, dy in cardinal_directions:
    try:
      sx = x + dx
      sy = y + dy
      if sx < 0 or sy < 0:
        continue
      if sector_map[sx, sy] == None:
        adjacent.append((sx,sy))
    except IndexError:
      # Out of bounds, ignore
      pass
  #print(f'The following sectors are adjacent to ({x},{y})')
  #print(adjacent)
  random.shuffle(adjacent)
  return adjacent

def tunnel_between(start, end, orientation):
  """ Return an S-shaped tunnel between these two points (x,y) """
  x1, y1 = start
  x2, y2 = end
  print(f'Building tunnel between ({x1},{y1}), and ({x2},{y2})')
  if orientation == 'h':
    corner1_x, corner1_y = (x1 + x2) // 2, y1
    corner2_x, corner2_y = corner1_x, y2
  else:
    # Move vertically, then horizontally.
    corner1_x, corner1_y = x1, (y1 + y2) // 2
    corner2_x, corner2_y = x2, corner1_y

  tunnel = []
  # Generate the coordinates for this tunnel.
  print(f'moving from  to ({corner1_x},{corner1_y})')
  for x, y in tcod.los.bresenham((x1, y1), (corner1_x, corner1_y)).tolist():
    tunnel.append((x, y))
  print(f'moving from ({corner1_x},{corner1_y}) to ({corner2_x},{corner2_y})')
  for x, y in tcod.los.bresenham((corner1_x, corner1_y), (corner2_x, corner2_y)).tolist():
    tunnel.append((x, y))
  print(f'moving from ({corner2_x},{corner2_y}) to ({x2},{y2})')
  for x, y in tcod.los.bresenham((corner2_x, corner2_y), (x2, y2)).tolist():
    tunnel.append((x, y))
  return tunnel


def place_interior_exits(tiles):
  for y, row in enumerate(tiles):
    for x, tile in enumerate(row):
      if tiles[x,y] == tile_types.floor_transition:
        #print('Found transition tile, building hall')
        # Find all ends
        # First find the adjacent hall tile
        hall_tile = find_first_adjacent(tiles, (x,y), tile_types.floor_hall)
        if not hall_tile:
          randchoice = random.random()
          if randchoice <= 0.5:
            tiles[x,y] = tile_types.wall
          elif randchoice <= 0.75:
            #print('Placing open floor')
            tiles[x, y] = tile_types.floor_hall
          else:
            #print('Placing closed door')
            tiles[x, y] = tile_types.door_closed

          #print('Found transition tile with no hallway!')
          # If for some reason we have a transition not adjacent to a hall tile,
          # just make it a wall
          #tiles[x,y] = tile_types.wall
          continue

        has_dead_ends = False
        exit_tiles = find_exit_tiles(tiles, hall_tile, tile_types.floor_transition)
        #print('Hallway has %s exits' % (len(exit_tiles)))
        for exit_tile in exit_tiles:
          # For each end, search the room for other exits
          exit_x, exit_y = exit_tile
          room_tile = find_first_adjacent(tiles, exit_tile, tile_types.floor_room)
          if not room_tile:
            print('Doorway with no room??')
            # If there's no room after the door well...
            tiles[exit_x, exit_y] = tile_types.wall
            continue
          room_exits = find_exit_tiles(tiles, room_tile, tile_types.floor_transition)
          #print('Room has %s exits' % (len(room_exits)))
          if len(room_exits) == 1:
            # We only found ourselves, so this is a dead end
            has_dead_ends = True
            break

        if has_dead_ends:
          #print('Found dead end.  Opening hallway.')
          # If at least one room at the end of this hall has no other
          # exits, choose a door or open end
          for x, y in exit_tiles:
            if random.random() <= 0.5:
              #print('Placing open floor')
              tiles[x, y] = tile_types.floor_hall
            else:
              #print('Placing closed door')
              tiles[x, y] = tile_types.door_closed

        else:
          # If there are other exits, also possibly place a wall.
          if random.random() <= 0.6:
            #print('Sealing off hallway')
            # Sealed off hallway.  We may want to fill this later
            # depending on what it looks like when breaches are applied
            fill_hall_start = find_first_adjacent(tiles, exit_tiles[0], tile_types.floor_hall)
            hall_tiles = flood_find(tiles, fill_hall_start)
            #print(fill_hall_start, hall_tiles)
            for x,y in hall_tiles:
              tiles[x,y] = tile_types.wall
            for x, y in exit_tiles:
              tiles[x,y] = tile_types.wall
          else:
            for x, y in exit_tiles:
              if random.random() <= 0.5:
                #print('Placing open floor')
                tiles[x, y] = tile_types.floor_hall
              else:
                #print('Placing closed door')
                tiles[x, y] = tile_types.door_closed

def find_rooms(dungeon, x1, y1, x2, y2):
  # Search all tile in rectangle (x1,y1),(x2,y2) and flood fill
  # any rooms, storing off their coords
  rooms = []
  found_coords = set()
  tiles = dungeon.tiles
  for x in range (x1, x2):
    for y in range(y1,y2):
      if (x,y) not in found_coords:
        if tiles[x,y] == tile_types.floor_room:
          room_tiles = flood_find(tiles, (x, y))
          room = Room(room_tiles)
          rooms.append(room)
          found_coords.update(room_tiles)
  return rooms

def find_first_adjacent(tiles, start_xy, search_type):
  x, y = start_xy
  for dx, dy in cardinal_directions:
    try:
      if tiles[x+dx,y+dy] == search_type:
        return (x+dx,y+dy)
        break
    except IndexError:
      # Tried to search out of map bounds
      pass
  return None

def flood_find(tiles, start_xy):
  """ return a list of all tiles connected to this tile of the same type """
  #print('Starting a flood find...')
  flood = []
  x, y = start_xy
  searched = set()
  to_search = set()
  to_search.add((x,y))
  search_type = tiles[x,y]
  #print(f"...search type {search_type}...")
  while len(to_search) > 0:
    x,y = to_search.pop()

    searched.add((x,y))
    for dx, dy in cardinal_directions:
      sx = x + dx
      sy = y + dy
      if ((sx,sy)) not in searched:
        #print('searching new tile')
        try:
          tile = tiles[sx,sy]
          if tile == search_type:
            to_search.add((sx,sy))
        except IndexError:
          # Edge of map, ignore
          pass
  #print('...ending a flood find!')
  return list(searched)

def find_exit_tiles(tiles, start_xy, exit_type):
  """ Used to find transition tiles at the end of hallways, airlocks,
      and rooms.
      Start at tile (x,y) and find all adjacent tiles of the same
      type. Add to search path.  Continue until you've found all tiles
      of end type touching them."""
  x, y = start_xy
  searched = flood_find(tiles, start_xy)
  exits = []
  for x, y in searched:
    for dx, dy in cardinal_directions:
      sx = x + dx
      sy = y + dy
      try:
        if tiles[sx,sy] == exit_type:
          exits.append((sx,sy))
      except IndexError:
        # Checked out of bounds of tiles
        pass
  return exits
