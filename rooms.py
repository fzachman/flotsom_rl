import random

# Maybe rooms should have a component system so we can add things like:
# Rooms with no exits and a vacuum that have a breakable wall between them and another room,
# so component would store conditional exit, maybe trigger condition that would alter map
# and exit path

class Room:
  def __init__(self, coords, walls, exits):
    """coords/walls/exits/connecting_rooms are all sets."""
    self.coords = coords # Basically walkable tiles in this room, floors and space usually
    self.walls = walls # Usefull if we have no exits to find a wall to place a door
    self.exits = exits
    self.is_vacuum_source = False # Changed later during map creation
    self.is_vacuum = False # Changed later during map creation


    # Prune internal exits that only lead to ourselves.
    removed = set()
    for x,y in self.exits:
      if ((x+1,y) in self.coords and (x-1,y) in self.coords) or \
         ((x,y-1) in self.coords and (x,y+1) in self.coords):
        # If both tiles along one axis are part of this room, this is
        # an internally connected door that doesn't lead to another room,
        # so remove it as an exit.
        removed.add((x,y))
    self.exits.difference_update(removed)

    self.connecting_rooms = set() # Filled in later by procgen using self.connect_if_able
    self.color = (random.randint(0,255),random.randint(0,255),random.randint(0,255)) # For map debugger
    self.min_x = 9999
    self.max_x = 0
    self.min_y = 9999
    self.max_y = 0
    for x, y in coords:
      if x < self.min_x:
        self.min_x = x
      if x > self.max_x:
        self.max_x = x
      if y < self.min_y:
        self.min_y = y
      if y > self.max_y:
        self.max_y = y

  @property
  def width(self):
    return self.max_x - self.min_x + 1

  @property
  def height(self):
    return self.max_y - self.min_y + 1

  def connect_if_able(self, other_room):
    if len(self.exits.intersection(other_room.exits)) > 0:
      self.connecting_rooms.add(other_room)
      other_room.connecting_rooms.add(self)

  def get_all_connections(self, connections=None):
    if not connections:
      connections = set([self])
    for r in self.connecting_rooms:
      if r not in connections:
        connections.add(r)
        connections.update(r.get_all_connections(connections))
    return connections
