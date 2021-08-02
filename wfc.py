import random
import io
import base64
from collections import namedtuple
import numpy as np
#from PIL import Image
#from IPython import display
import string

def blend_many(ims):
    """
    Blends a sequence of images.
    """
    current, *ims = ims
    for i, im in enumerate(ims):
        current = Image.blend(current, im, 1/(i+2))
    return current

def blend_tiles(choices, tiles):
    """
    Given a list of states (True if ruled out, False if not) for each tile,
    and a list of tiles, return a blend of all the tiles that haven't been
    ruled out.
    """
    to_blend = [tiles[i].bitmap for i in range(len(choices)) if choices[i]]
    return blend_many(to_blend)

def show_state(potential, tiles):
    """
    Given a list of states for each tile for each position of the image, return
    an image representing the state of the global image.
    """
    rows = []
    for row in potential:
        rows.append([np.asarray(blend_tiles(t, tiles)) for t in row])

    rows = np.array(rows)
    n_rows, n_cols, tile_height, tile_width, _ = rows.shape
    images = np.swapaxes(rows, 1, 2)
    return Image.fromarray(images.reshape(n_rows*tile_height, n_cols*tile_width, 4))

def find_true(array):
    """
    Like np.nonzero, except it makes sense.
    """
    transform = int if len(np.asarray(array).shape) == 1 else tuple
    return list(map(transform, np.transpose(np.nonzero(array))))

def get_all_rotations(tile):
    """
    Return original array as well as rotated by 90, 180 and 270 degrees in the form of tuples
    """
    tile_rotated_1 = np.rot90(tile).tolist()#[[tile[j][i] for j in range(len(tile))] for i in range(len(tile[0])-1,-1,-1)]
    tile_rotated_2 = np.rot90(tile,2).tolist()#[[tile_rotated_1[j][i] for j in range(len(tile_rotated_1))] for i in range(len(tile_rotated_1[0])-1,-1,-1)]
    tile_rotated_3 = np.rot90(tile,3).tolist()#[[tile_rotated_2[j][i] for j in range(len(tile_rotated_2))] for i in range(len(tile_rotated_2[0])-1,-1,-1)]
    #return tile, tile_rotated_1, tile_rotated_2, tile_rotated_3

    return (tuple(tuple(row) for row in tile), \
            tuple(tuple(row) for row in tile_rotated_1), \
            tuple(tuple(row) for row in tile_rotated_2), \
            tuple(tuple(row) for row in tile_rotated_3))

Tile = namedtuple('Tile', ('data','sides','weight'))
#letters = string.ascii_uppercase
def get_tile_sides(tile, tile_size):
  # Right, Up, Left, Down
  right = ''
  up    = ''
  left  = ''
  down  = ''
  for i in range(0, tile_size):
    right += '%03d' % (tile[i, tile_size -1])
    up    += '%03d' % (tile[0, i])
    left  += '%03d' % (tile[i, 0])
    down  += '%03d' % (tile[tile_size -1, i])
  return (right, up, left, down)

def create_tiles(source, tile_size=2):
  weights = {} # dict tiles -> occurence
  height = len(source)
  width = len(source[0])
  for y in range(height-(tile_size-1)): # row
      for x in range(width-(tile_size-1)): # column
          tile = source[x:x+tile_size,y:y+tile_size]
          #print(f'Tile: {tile}')
          tile_rotations = get_all_rotations(tile)
          #print(f'Rotations: {tile_rotations}')
          for rotation in tile_rotations:
              if rotation not in weights:
                  weights[rotation] = 1
              else:
                  weights[rotation] += 1

  tiles = []
  for tile, weight in weights.items():
    #print(f'{tile}, {np.array(tile)}, weight')
    tile = np.array(tile)
    sides = get_tile_sides(tile, tile_size)
    #print(tile, sides)
    tiles.append(Tile(tile, sides , weight))
  #print(tiles)
  return tiles

def run_iteration(tiles, weights, old_potential):
    potential = old_potential.copy()
    to_collapse = location_with_fewest_choices(potential) #3
    if to_collapse is None:                               #1
        raise StopIteration()
    elif not np.any(potential[to_collapse]):              #2
        raise Exception(f"No choices left at {to_collapse}")
    else:                                                 #4 ↓
        #nonzero = find_true(potential[to_collapse])
        #tile_probs = weights[nonzero]/sum(weights[nonzero])
        #selected_tile = np.random.choice(nonzero, p=tile_probs)
        #potential[to_collapse] = False
        #potential[to_collapse][selected_tile] = True
        #propagate(tiles, potential, to_collapse)                 #5
        potential = collapse(tiles, weights, potential, to_collapse)
    return potential

def collapse(tiles, weights, potential, to_collapse):
  nonzero = find_true(potential[to_collapse])
  tile_probs = weights[nonzero]/sum(weights[nonzero])
  selected_tile = np.random.choice(nonzero, p=tile_probs)
  #print(f'{to_collapse} is now {tiles[selected_tile]}')
  #import pdb; pdb.set_trace()
  potential[to_collapse] = False
  potential[to_collapse][selected_tile] = True
  propagate(tiles, potential, to_collapse)
  return potential

def location_with_fewest_choices(potential):
    num_choices = np.sum(potential, axis=2, dtype='float32')
    num_choices[num_choices == 1] = np.inf
    candidate_locations = find_true(num_choices == num_choices.min())
    location = random.choice(candidate_locations)
    if num_choices[location] == np.inf:
        return None
    return location

from enum import Enum, auto

class Direction(Enum):
    RIGHT = 0; UP = 1; LEFT = 2; DOWN = 3

    def reverse(self):
        return {Direction.RIGHT: Direction.LEFT,
                Direction.LEFT: Direction.RIGHT,
                Direction.UP: Direction.DOWN,
                Direction.DOWN: Direction.UP}[self]

def neighbors(location, height, width):
    res = []
    x, y = location
    if x != 0:
        res.append((Direction.UP, x-1, y))
    if y != 0:
        res.append((Direction.LEFT, x, y-1))
    if x < height - 1:
        res.append((Direction.DOWN, x+1, y))
    if y < width - 1:
        res.append((Direction.RIGHT, x, y+1))
    return res

def propagate(tiles, potential, start_location):
    height, width = potential.shape[:2]
    needs_update = np.full((height, width), False)
    needs_update[start_location] = True
    while np.any(needs_update):
        needs_update_next = np.full((height, width), False)
        locations = find_true(needs_update)
        for location in locations:
            #import pdb; pdb.set_trace()
            possible_tiles = [tiles[n] for n in find_true(potential[location])]
            #print(possible_tiles)
            for neighbor in neighbors(location, height, width):
                neighbor_direction, neighbor_x, neighbor_y = neighbor
                neighbor_location = (neighbor_x, neighbor_y)
                was_updated = add_constraint(tiles, potential, neighbor_location,
                                             neighbor_direction, possible_tiles)
                needs_update_next[location] |= was_updated
        needs_update = needs_update_next

def add_constraint(tiles, potential, location, incoming_direction, possible_tiles):
    neighbor_constraint = {t.sides[incoming_direction.value] for t in possible_tiles}
    outgoing_direction = incoming_direction.reverse()
    changed = False
    #print(f'Checking neighbor against {neighbor_constraint}')
    for i_p, p in enumerate(potential[location]):
        if not p:
            continue
        #print(f'Searching for {tiles[i_p].sides[outgoing_direction.value]} in {neighbor_constraint}')
        if tiles[i_p].sides[outgoing_direction.value] not in neighbor_constraint:
            #print(f'Invalid {tiles[i_p].sides[outgoing_direction.value]}')
            potential[location][i_p] = False
            changed = True
        #else:
          #print(f'Valid {tiles[i_p].sides[outgoing_direction.value]}')
    #import pdb; pdb.set_trace()
    #print(f'{potential[location]}, {np.any(potential[location])}')
    if not np.any(potential[location]):
        raise Exception(f"No patterns left at {location}")
    return changed

def get_wfc(source=None, tiles=[], tile_size=2, width=20, height=20):
  if source is not None:
    tiles = create_tiles(source, tile_size)

  weights = np.asarray([t.weight for t in tiles])
  #for t in tiles:
  #  print(t.weight, t.data)
  p = np.full((height, width, len(tiles)), True)

  tries = 0
  while tries < 5000:
      try:
          p = run_iteration(tiles, weights, p)
          #images.append(show_state(p, tiles))  # Move me for speed
      except StopIteration as e:
          break
      except:
        p = np.full((height, width, len(tiles)), True)
      tries += 1

  print(tries)
  p = p.tolist()
  pixels = np.full((height * (tile_size), width * (tile_size)), 0)
  #print(len(p), len(pixels), len(p[0]), len(pixels[0]))
  rows = []
  for x, row in enumerate(p):
    #print(x, row)
    new_row = []
    for y, r in enumerate(row):
      for t, tf in enumerate(r):
        if tf:
          #print(tiles[t].data)
          #print(x, y, x*tile_size, x*tile_size+tile_size, y*tile_size, y*tile_size+tile_size, len(pixels), len(pixels[0]))
          pixels[x*(tile_size):x*(tile_size)+tile_size,y*(tile_size):y*(tile_size)+tile_size] = tiles[t].data
          #new_row.append(tiles[t])
    #rows.append(new_row)

  #print('\n'.join([''.join(str(c) for c in r) for r in pixels.tolist()]))
  return pixels


if __name__ == '__main__':
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
  print(get_wfc(source))
