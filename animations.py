from time import sleep
import color
import tcod
from collections import deque


class Animation:
  def __init__(self, entity):
    self.entity = entity

  def animate(self, console, dungeon):
    raise NotImplementedError


class DamagedAnimation(Animation):
  def __init__(self, entity, color=color.damage_default):
    super().__init__(entity)
    self.color = color
  def animate(self, console, engine):
    viewport = engine.game_map.get_viewport()
    entity = self.entity
    x = entity.x - viewport[0]
    y = entity.y - viewport[1]
    original_bg_color = console.tiles_rgb['bg'][x,y]
    color1 = self.color
    color2 = []
    for c in color1:
      color2.append(c//2)
    color2 = tuple(color2)
    colors = (color1,color2)
    for i in range(2):
      console.tiles_rgb['bg'][x,y] = colors[i % 2]
      sleep(.025)
      yield console

    console.tiles_rgb['bg'][x,y] = original_bg_color
    yield console

class MeleeAnimation(Animation):
  def animate(self, console, engine):
    viewport = engine.game_map.get_viewport()
    entity = self.entity
    x = entity.x - viewport[0]
    y = entity.y - viewport[1]
    original_fg_color = console.tiles_rgb['fg'][x,y].copy()
    colors = ((255,255,255), original_fg_color)
    for i in range(2):
      console.tiles_rgb['fg'][x,y] = colors[i % 2]
      sleep(.025)
      yield console

    console.tiles_rgb['fg'][x,y] = original_fg_color
    #sleep(.025)
    yield console

class RangedAnimation(Animation):
  def __init__(self, entity, target):
    super().__init__(entity)
    self.target = target

  def animate(self, console, engine):
    viewport = engine.game_map.get_viewport()
    entity = self.entity
    target = self.target
    start_x = entity.x
    start_y = entity.y
    end_x = target.x
    end_y = target.y
    line = tcod.los.bresenham((start_x, start_y), (end_x, end_y)).tolist()[1:-1]
    #print(line)
    original = deque()
    for x,y in line:
      x -= viewport[0]
      y -= viewport[1]
      print(x,y)
      if len(original) > 1:
        # Restore the previous tile
        xy, data = original.popleft()
        #print(f'Restoring original tile {xy} to {data}')
        self._restore_tile(console, xy, data)

      bg = console.tiles_rgb['bg'][x,y].copy()
      fg = console.tiles_rgb['fg'][x,y].copy()
      ch = console.ch[x,y]
      #print(f'Storing original tile ({x},{y}) as ({bg},{fg},{ch})')
      original.append(((x,y),(bg,fg,ch)))

      console.tiles_rgb['bg'][x,y] = (192,192,255)
      console.tiles_rgb['fg'][x,y] = (255,255,255)
      console.ch[x,y] = ord('*')
      sleep(.05)
      yield console

    while len(original) > 0:
       xy, data = original.popleft()
       self._restore_tile(console, xy, data)
       sleep(.025)
       yield console

    yield console

  def _restore_tile(self, console, xy, data):
    x, y = xy
    bg, fg, ch = data
    console.tiles_rgb['bg'][x,y] = bg
    console.tiles_rgb['fg'][x,y] = fg
    console.ch[x,y] = ch
