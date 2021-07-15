import numpy as np


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
    ('tile_name', np.unicode_, 16)
  ]
)

def new_tile(*,  # Enforce the use of keywords, so that parameter order doesn't matter.
             walkable,
             transparent,
             dark,
             light,
             tile_name):
    """Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light, tile_name), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(' '), (255,255,255), (0,0,0)), dtype=graphic_dt)

floor_room = new_tile(walkable = True, transparent = True,
                      dark=(ord(' '), (255,255,255), (90,110,110)),
                      light=(ord(' '), (255, 255, 255), (175, 210, 210)),
                      tile_name='floor_room'
                      )

floor_hall = new_tile(walkable = True, transparent = True,
                      dark=(ord(' '), (255,255,255), (80,100,100)),
                      light=(ord(' '), (255, 255, 255), (165, 200, 200)),
                      tile_name='floor_hall'
                      )

floor_airlock = new_tile(walkable = True, transparent = True,
                        dark=(ord(' '), (255,255,255), (100,100,100)),
                        light=(ord(' '), (255, 255, 255), (200, 200, 200)),
                        tile_name='floor_airlock'
                        )

floor_transition = new_tile(walkable = True, transparent = True,
                            dark=(ord(' '), (255,255,255), (100,100,0)),
                            light=(ord(' '), (255, 255, 255), (200, 200, 0)),
                            tile_name='floor_transition'
                            )

exit_point = new_tile(walkable = False, transparent = False,
                      dark=(ord(' '), (255,255,255), (100,0,0)),
                      light=(ord(' '), (255, 255, 255), (200, 0, 0)),
                      tile_name='exit_point'
                      )

wall = new_tile(walkable=False, transparent=False,
                dark=(ord(' '), (255,255,255),(45,50,50)),
                light=(ord(' '), (255, 255, 255), (150, 173, 173)),
                tile_name='wall'
                )

door_open = new_tile(walkable = True, transparent = True,
                 dark=(ord('_'), (255,255,255), (90,110,110)),
                 light=(ord('_'), (255, 255, 255), (175, 210, 210)),
                 tile_name='door_open'
                 )

door_closed = new_tile(walkable = False, transparent = False,
                 dark=(ord('#'), (255,255,255), (90,110,110)),
                 light=(ord('#'), (255, 255, 255), (175, 210, 210)),
                 tile_name='door_closed'
                 )


down_stairs = new_tile(walkable=True,
                       transparent=True,
                       dark=(ord('>'), (0, 0, 100), (50,50,150)),
                       light=(ord('>'), (255,255,255),(200,180,50)),
                       tile_name='down_stairs'
                       )
