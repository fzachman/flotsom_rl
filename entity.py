import copy
import math
from render_order import RenderOrder
from components.ai import ChainedAI

class Entity:
  """
  A generic object to represent players, enemies, items, etc.
  """
  def __init__(self,
               parent = None,
               x = 0,
               y = 0,
               char = '?',
               color = (255,255,255),
               name='<Unnamed>',
               blocks_movement=False,
               render_order=RenderOrder.CORPSE,
               light_source = None):
    self.x = x
    self.y = y
    self.char = char
    self.color = color
    self.name = name
    self.blocks_movement = blocks_movement
    self.render_order = render_order
    self.light_source = light_source
    if light_source:
      self.light_source.parent = self

    if parent:
      # If parent isn't provided now then it will be set later.
      self.parent = parent
      parent.entities.add(self)

  @property
  def gamemap(self):
    return self.parent.gamemap

  def spawn(self, gamemap, x, y):
    """ Spawn a copy of this instance at the given location """
    clone = copy.deepcopy(self)
    clone.x = x
    clone.y = y
    clone.parent = gamemap
    gamemap.entities.add(clone)
    return clone

  def place(self, x, y, gamemap = None):
    """ Place this entity at a new location.  Handles moving across GameMaps."""
    self.x = x
    self.y = y
    if gamemap:
      if hasattr(self, 'parent'): # Possibly uninitialized
        if self.parent is self.gamemap:
          self.gamemap.entities.remove(self)
      self.parent = gamemap
      gamemap.entities.add(self)

  def distance(self, x, y):
    """Return the distance between current entity and given coords."""
    return math.sqrt((x - self.x) ** 2 + (y - self.y) **2)

  def move(self, dx, dy):
    # Move the entity by a given amount
    self.x += dx
    self.y += dy

class Actor(Entity):
  def __init__(self,
               *,
               x = 0,
               y = 0,
               char = '?',
               color = (255,255,255),
               name = '<Unnamed>',
               visibility=40,
               ai_cls,
               equipment,
               fighter,
               inventory,
               level,
               lungs,
               lootable,
               light_source=None):
    super().__init__(
      x=x,
      y=y,
      char=char,
      color=color,
      name=name,
      blocks_movement=True,
      render_order=RenderOrder.ACTOR,
      light_source=light_source
    )


    self.visibility = visibility

    if type(ai_cls) == list:
      ai = ChainedAI(self, ai_cls)
    else:
      ai = ai_cls(self)
    self.ai = ai

    self.equipment = equipment
    self.equipment.parent = self

    self.fighter = fighter
    self.fighter.parent = self

    self.inventory = inventory
    self.inventory.parent = self

    self.level = level
    self.level.parent = self

    self.lungs = lungs
    self.lungs.parent = self

    self.lootable = lootable
    self.lootable.parent = self

  @property
  def is_alive(self):
    return bool(self.ai)

class Item(Entity):
  def __init__(self,
               *,
               x = 0,
               y = 0,
               char = '?',
               color = (255,255,255),
               name = '<Unnamed>',
               consumable=None,
               equippable=None,
               powered=None):
    super().__init__(
      x=x,
      y=y,
      char=char,
      color=color,
      name=name,
      blocks_movement=False,
      render_order=RenderOrder.ITEM,
    )
    self.consumable = consumable
    if self.consumable:
      self.consumable.parent = self

    self.equippable = equippable
    if self.equippable:
      self.equippable.parent = self

    self.powered = powered
    if self.powered:
      self.powered.parent = self

class Container(Entity):
  def __init__(self,
               *,
               x = 0,
               y = 0,
               char='?',
               color= (255,255,255),
               name = '<Container>',
               lootable):
    super().__init__(
      x=x,
      y=y,
      char=char,
      color=color,
      name=name,
      blocks_movement=True,
      render_order=RenderOrder.DECORATION,
    )
    self.lootable = lootable
    self.lootable.parent = self

  def add_items(self, items):
    if type(items) == Item:
      items = [items]
    self.items.extend(items)
