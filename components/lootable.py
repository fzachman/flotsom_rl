from components.base_component import BaseComponent
import exceptions
import color


class Lootable(BaseComponent):
  def __init__(self, items=[]):
    self.items = items

  def loot(self):
    if len(self.items) == 0:
      self.engine.message_log.add_message("It's empty!")
      return

    droppable = []
    for dx, dy in ((1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)):
      lx = self.parent.x + dx
      ly = self.parent.y + dy
      if self.gamemap.in_bounds(lx, ly) and self.gamemap.tiles[lx, ly]['walkable']:
        droppable.append((lx,ly))
    to_drop = items[:len(droppable)]
    for item in to_drop:
      x, y = droppable.pop()
      self.items.remove(item)
      item.place(x, y, self.gamemap)
