def get_tile_bit_code(tiles):
  """Given a 3x3 grid of tiles, return a bit code that uniquely
  identifies the configuration of walls in this tile group."""
  code = 0
  v = 1
  for x in range(3):
    for y in range(3):
      if x == 1 and y == 1:
        # Ignore the center tile
        continue
      if tiles[x,y]['tile_class'] == 'wall' or tiles[x,y]['tile_class'] == 'door':
        code += v
      v = v * 2
  return code

# mask is what bits we care about.  255 cares about every tile position.  Might not be needed...
# subclasses are named based on connection points. ╔ connects down and right, thus is a 'dr'
# Internally, the array is represented rotated 180, so some of these don't entirely make sense

codes = [# Most restrictive
         {'subclass': 'x', 'mask': 255, 'bit_codes': [90, 91, 94, 122, 218]}, # 4 way

         {'subclass': 'tl', 'mask': 255, 'bit_codes': [26, 250]}, #T with left connection
         {'subclass': 'tu', 'mask': 255, 'bit_codes': [74, 222]}, # T with upper connection
         {'subclass': 'tr', 'mask': 255, 'bit_codes': [88, 95]}, # T with right connection
         {'subclass': 'td', 'mask': 255, 'bit_codes': [82, 123]}, # T with down connection

         {'subclass': 'h', 'mask': 255, 'bit_codes': [248, 31, 24]},
         {'subclass': 'v', 'mask': 255, 'bit_codes': [214, 107, 66]},

         {'subclass': 'ul', 'mask': 255, 'bit_codes': [254, 10]}, # Up and Left connections
         {'subclass': 'dl', 'mask': 255, 'bit_codes': [251, 22]}, # Up and Right
         {'subclass': 'ur', 'mask': 255, 'bit_codes': [223, 104]}, # Down and Left
         {'subclass': 'dr', 'mask': 255, 'bit_codes': [127, 208]}, # Down and Right

         # Less Restrictive checks go here
         {'subclass': 'tl', 'mask': 95, 'bit_codes': [26, 27, 30]}, #T with left connection
         {'subclass': 'tu', 'mask': 123, 'bit_codes': [74, 75, 106]}, # T with upper connection
         {'subclass': 'tr', 'mask': 250, 'bit_codes': [88, 120, 216]}, # T with right connection
         {'subclass': 'td', 'mask': 222, 'bit_codes': [82, 86, 210]}, # T with down connection


         {'subclass': 'h', 'mask': 95, 'bit_codes': [24]},
         {'subclass': 'h', 'mask': 250, 'bit_codes': [24]},
         {'subclass': 'v', 'mask': 123, 'bit_codes': [66]},
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

mapped_codes = {}

def get_wall_subclass_for_bit_code(bit_code):
  """Given a bit code from the above function, find the correct wall
  shape to put in its place.  A bit code of 11111110 represents a tile group
  who's walls are here:
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
