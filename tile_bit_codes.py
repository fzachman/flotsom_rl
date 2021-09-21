def get_tile_bit_code(tiles, ignore_center=True, tile_classes=['wall','door']):
  """Given a grid of tiles, generate a bit code where each tile that matches
  any of the tile_classes will be an ON bit, and any other tile will be an OFF.

  So for a 3x3 array that ignores the center tile, it generates an 8 bit code, ie.
  0 (binary 00000000) if no tiles match, to 256 (binary 11111111) if every tile matches.

  Supports any sized array, but behavior can be weird if you pass in
  an array with even sized dimensions (ie. 4x4) and ignore_center == True due
  to not having an actual center..."""
  code = 0 # The actual code we will be returning, initialized to 00000000
  width = len(tiles)
  height = len(tiles[0])
  # This works because for a 3x3 tile, 3//2 == 1, and while 1 wouldn't be the middle
  # of 1,2,3, it *is* the middle index of array [0,1,2]
  # If you "ignore_center" of an even dimensional array, no guarantees what happens :P
  center_x = width // 2
  center_y = height // 2
  v = 1 # The current "bit" we're processing, represented as an int.
  for x in range(width):
    for y in range(height):
      if ignore_center and x == center_x and y == center_y:
        # Ignore the center tile
        continue
      if tiles[x,y]['tile_class'] in tile_classes:
        # This is a tile class we care about, so toggle this tiles bit
        code += v
      v = v * 2 # Bit shift for next iteration
  return code

# mask is what bits we care about.  255 cares about every tile position and results in the most
# restrictive check.  ie. if the tile configuration is exactly this in every position, draw this
# wall.  Less restrictive bit codes are processed after more restrictive, so as we get farther and
# farther down the chain, we look at fewer tiles in the pattern to determine what should be there.

# subclasses are named based on connection points. ╔ connects down and right, thus is a 'dr'
# Internally, the array is represented with X being down and Y being across, so the mappings
# are a bit confusing.

codes = [# Most restrictive
         {'subclass': 'x', 'mask': 255, 'bit_codes': [90, 91, 94, 122, 218]}, # 4 way

         {'subclass': 'tl', 'mask': 255, 'bit_codes': [26, 250]}, #T with left connection
         {'subclass': 'tu', 'mask': 255, 'bit_codes': [74, 222]}, # T with upper connection
         {'subclass': 'tr', 'mask': 255, 'bit_codes': [88, 95]}, # T with right connection
         {'subclass': 'td', 'mask': 255, 'bit_codes': [82, 123]}, # T with down connection
         {'subclass': 'pillar', 'mask': 255, 'bit_codes': [0]},

         {'subclass': 'h', 'mask': 255, 'bit_codes': [248, 31, 24]}, # Horizontal wall
         {'subclass': 'v', 'mask': 255, 'bit_codes': [214, 107, 66]}, # Vertical wall

         {'subclass': 'ul', 'mask': 255, 'bit_codes': [254, 10]}, # Up and Left connections
         {'subclass': 'dl', 'mask': 255, 'bit_codes': [251, 22]}, # Up and Right
         {'subclass': 'ur', 'mask': 255, 'bit_codes': [223, 104]}, # Down and Left
         {'subclass': 'dr', 'mask': 255, 'bit_codes': [127, 208]}, # Down and Right

         # Less Restrictive checks go here
         {'subclass': 'tl', 'mask': 95, 'bit_codes': [26, 27, 30]}, #T with left connection
         {'subclass': 'tu', 'mask': 123, 'bit_codes': [74, 75, 106]}, # T with upper connection
         {'subclass': 'tr', 'mask': 250, 'bit_codes': [88, 120, 216]}, # T with right connection
         {'subclass': 'td', 'mask': 222, 'bit_codes': [82, 86, 210]}, # T with down connection


         {'subclass': 'h', 'mask': 95, 'bit_codes': [24]}, # Horizontal wall
         {'subclass': 'h', 'mask': 250, 'bit_codes': [24]},
         {'subclass': 'v', 'mask': 123, 'bit_codes': [66]}, # Vertical wall
         {'subclass': 'v', 'mask': 222, 'bit_codes': [66]},

         {'subclass': 'ul', 'mask': 91, 'bit_codes': [90]}, # Up and Left connections
         {'subclass': 'dl', 'mask': 94, 'bit_codes': [90]}, # Up and Right
         {'subclass': 'ur', 'mask': 122, 'bit_codes': [90]}, # Down and Left
         {'subclass': 'dr', 'mask': 218, 'bit_codes': [90]}, # Down and Right

         {'subclass': 'ul', 'mask': 218, 'bit_codes': [10]}, # Up and Left connections
         {'subclass': 'dl', 'mask': 122, 'bit_codes': [18]}, # Up and Right
         {'subclass': 'ur', 'mask': 94, 'bit_codes': [72]}, # Down and Left
         {'subclass': 'dr', 'mask': 91, 'bit_codes': [80]}, # Down and Right

         # Even less restrictive
         {'subclass': 'v', 'mask': 90, 'bit_codes': [66, 74, 82]}, # Vertical wall
         {'subclass': 'h', 'mask': 90, 'bit_codes': [24, 26, 88]}, # Horizontal wall
         # Least Restrictive
         {'subclass': 'v', 'mask': 24, 'bit_codes': [0]}, # Vertical wall
         {'subclass': 'h', 'mask': 66, 'bit_codes': [0]}, # Horizontal wall

         ]

# A little lookup cache so we don't have to perform the checks
# on previously mapped patterns.
mapped_codes = {}

def get_wall_subclass_for_bit_code(bit_code):
  """Given a bit code from the above function, find the correct wall
  shape to put in its place.  A bit code of 127 (11111110) represents a
  tile group who's walls are here:
  WWW
  W*W
  WWF
  The central * tile should be a ╔"""
  subclass = mapped_codes.get(bit_code)
  if not subclass:
    for code in codes:
      mask = code['mask']
      masked_bits = bit_code & mask
      if masked_bits in code['bit_codes']:
        subclass = code['subclass']
        mapped_codes[bit_code] = subclass
        break
  return subclass
