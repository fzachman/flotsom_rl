import random

import numpy as np
import tcod

from actions import Action, BumpAction, MeleeAction, TargetedRangedAttack, MovementAction, WaitAction, ActivateAction

class BaseAI(Action):
  def perform(self):
    raise NotImplementedError()

  def get_path_to(self, dest_x, dest_y):
    """ Compute and return a path to the target position.
    If there is no valid path, then return an empty list."""

    # Copy the walkable array
    cost = np.array(self.entity.gamemap.tiles['walkable'], dtype=np.int8)
    doors = np.where(self.entity.gamemap.tiles['tile_subclass'] == 'closed', 2, 0)
    for x in range(0, len(doors)-1):
      for y in range(0, len(doors[0]) -1):
        cost[x][y] = cost[x][y] + doors[x][y]

    for entity in self.entity.gamemap.entities:
      # Check that an entity blocks movement and the cost isn't zero (blocking)
      if entity.blocks_movement and cost[entity.x, entity.y]:
        # Add to the cost of a blocked position
        # A lower number means more enemies will crowd behind each other in
        # hallways.  A higher number means enemeies will take longer paths in
        # order to surround the player
        cost[entity.x, entity.y] += 10

    graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
    pathfinder = tcod.path.Pathfinder(graph)

    pathfinder.add_root((self.entity.x, self.entity.y)) # Start position

    # Compute a path to the destination and remove the starting point
    path = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

    # Convert from List[List[int]] to List[Tuple[int,int]]
    return [(index[0], index[1]) for index in path]

  def is_next_to(self, x, y):
    if self.entity.x - x in (-1,0,1) and self.entity.y - y in (-1,0,1):
      return True
    else:
      return False

class TemporaryAI(BaseAI):
  """Allows an entity to receive a temporary change in AI that lasts
  for a certain number of turns and then expires, restoring their original
  AI"""
  def __init__(self, entity, previous_ai, new_ai, turns_remaining, expire_message=None):
    super().__init__(entity)
    self.previous_ai = previous_ai
    self.new_ai = new_ai
    self.turns_remaining = turns_remaining
    self.expire_message = expire_message

  def perform(self):
    if self.turns_remaining <= 0:
      if self.expire_message:
        self.engine.message_log.add_message(self.expire_message)
      self.entity.ai = self.previous_ai
      return self.previous_ai.perform()
    else:
      self.turns_remaining -= 1
      return self.new_ai.perform()



class ConfusedEnemey(BaseAI):
  """
  A confused enemy will stumble around aimlessly for a given number of turns,
  then revert back to its previous AI.
  If an actor occupies a tile it is randomly moving into, it will attack.
  """

  def __init__(self, entity, previous_ai=None, turns_remaining=0):
    super().__init__(entity)
    self.previous_ai = previous_ai
    self.turns_remaining = turns_remaining

  def perform(self):
    direction_x, direction_y = random.choice(
      [
        (-1, -1),  # Northwest
        (0, -1),  # North
        (1, -1),  # Northeast
        (-1, 0),  # West
        (1, 0),  # East
        (-1, 1),  # Southwest
        (0, 1),  # South
        (1, 1),  # Southeast
      ]
    )

    # The actor will either try to move or attack in the chosen random direction.
    # Its possible the actor will just bump into the wall, wasting a turn.
    return BumpAction(self.entity, direction_x, direction_y,).perform()

class HostileEnemy(BaseAI):
  def __init__(self, entity):
    super().__init__(entity)
    self.path = []

  def perform(self):
    target = self.engine.player
    dx = target.x - self.entity.x
    dy = target.y - self.entity.y
    distance = max(abs(dx), abs(dy)) # Chebyshev distance

    if self.engine.game_map.visible[self.entity.x, self.entity.y]:
      if distance <= 1:
        return MeleeAction(self.entity, dx, dy).perform()

      self.path = self.get_path_to(target.x, target.y)

    if self.path:
      dest_x, dest_y = self.path.pop(0)
      return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

    return WaitAction(self.entity).perform()

class RangedEnemy(BaseAI):
  def __init__(self, entity, range):
    super().__init__(entity)
    self.range = range
    self.path = []

  def perform(self):
    target = self.engine.player
    dx = target.x - self.entity.x
    dy = target.y - self.entity.y
    distance = max(abs(dx), abs(dy)) # Chebyshev distance

    if self.engine.game_map.visible[self.entity.x, self.entity.y]:
      self.path = self.get_path_to(target.x, target.y)
      if distance <= self.range:
        return TargetedRangedAttack(self.entity, (target.x, target.y)).perform()


    if self.path:
      dest_x, dest_y = self.path.pop(0)
      return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

    return WaitAction(self.entity).perform()

class Shooter(RangedEnemy):
  def __init__(self, entity):
    super().__init__(entity, 10)

class Sniper(RangedEnemy):
  def __init__(self, entity):
    super().__init__(entity, 20)

class ChainedAI(BaseAI):
  def __init__(self, entity, ai_classes):
    super().__init__(entity)
    self.ai_classes = []
    for ai_cls in ai_classes:
      self.ai_classes.append(ai_cls(entity))

  def perform(self):
    for ai_cls in self.ai_classes:
      result = ai_cls.perform()
      if result is not None:
        return result
    return WaitAction(self.entity).perform()

class Breather(BaseAI):
  def __init__(self, entity):
    super().__init__(entity)

  def perform(self):
    my_location = (self.entity.x, self.entity.y)
    if my_location in self.engine.game_map.vacuum_tiles:
      # On no, I'm in a vacuum!
      #print(f'I cannot breath! {my_location}')
      my_room = self.engine.game_map.get_room_at_location(my_location)
      if my_room is None:
        # Probably standing in a doorway
        # Find a non vacuum source room next to us
        for d_x, d_y in [(-1,0),(1,0),(0,1),(0, -1)]:
          my_room = self.engine.game_map.get_room_at_location((self.entity.x + d_x, self.entity.y + d_y))
          if my_room and my_room.is_vacuum_source:
            # This is the room we want to run from!
            break
      if not my_room:
        #print('I do not know what room I am in!')
        return None
      if my_room.is_vacuum_source:
        # Leave this room!
        #print('The hole is in this room!  Run!')
        for neighbor in my_room.connecting_rooms:
          if not neighbor.is_vacuum_source:
            n_x, n_y = list(neighbor.coords)[0]
            # Need the ability to open doors.
            path = self.get_path_to(n_x, n_y)
            #print(f'Path to {n_x}, {n_y}: {path}')
            if path:
              dest_x, dest_y = path.pop(0)
              #print(f'Running to ({dest_x},{dest_y}) via ({dest_x - self.entity.x, dest_y - self.entity.y}')
              return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()
      else:
        # Close some doors!
        #print('Who left the door open??')
        for e_x, e_y in my_room.exits:
          exit = self.engine.game_map.tiles[e_x, e_y]
          if exit['tile_class'] == 'door' and exit['tile_subclass'] == 'open':
            if self.is_next_to(e_x, e_y):
              #print('I will close it!')
              return ActivateAction(self.entity).perform()
            else:
              path = self.get_path_to(e_x, e_y)
              #print(f'Heading to door at ({e_x},{e_y}) via {path}')
              if path:
                #print('Heading to the door!')
                dest_x, dest_y = path.pop(0)
                return MovementAction(self.entity, dest_x - self.entity.x, dest_y - self.entity.y).perform()

    return None


class Drifting(BaseAI):
  def __init__(self, entity, momentum, parent_ai):
    super().__init__(entity)
    self.momentum = momentum
    self.parent_ai = parent_ai

  def perform(self):
    dx, dy = self.momentum
    gamemap = self.entity.parent.gamemap

    x = self.entity.x + dx
    y = self.entity.y + dy

    spaced = False
    if not gamemap.in_bounds(x, y):
      # If this entity drifts off the map, they're dead.
      # For now we'll just die.  Later we probably want to clean up the entity
      spaced = True
    else:
      # Check to see if we're hitting a wall and reverse our momentum
      if dx == 0 or dy == 0:
        # If we're going straight, just check if we're hitting a wall and bounce back
        if self._is_blocked(x,y):
          if dx != 0:
            dx = dx < 0 and 1 or -1
          elif dy != 0:
            dy = dy < 0 and 1 or -1
          self.momentum = (dx, dy)
      else:
        # If we're moving at an angle, we need to check to walls, not the diagonal one
        # and we bounce of each one
        if not gamemap.in_bounds(x, self.entity.y) or not gamemap.in_bounds(self.entity.x, y):
          spaced = True
        else:
          if self._is_blocked(x, self.entity.y):
            dx = dx < 0 and 1 or -1
          if self._is_blocked(self.entity.x, y):
            dy = dy < 0 and 1 or -1

          x = self.entity.x + dx
          y = self.entity.y + dy
          if not gamemap.in_bounds(x,y):
            spaced = True
          elif self._is_blocked(x,y):
            # If we're bouncing into *another* wall, we have issues.
            # We'd like to just reverse our original direction since that's safe. But
            # You can get caught in a loop this way, so first check to see if we can slide onto a floor
            if gamemap.in_bounds(self.entity.x + dx, self.entity.y) and \
               gamemap.tiles[self.entity.x + dx, self.entity.y]['tile_class'] == 'floor':
              dy = 0
            elif gamemap.in_bounds(self.entity.x, self.entity.y + dy) and \
               gamemap.tiles[self.entity.x, self.entity.y + dy]['tile_class'] == 'floor':
              dx = 0
            else:
              # No floor, just reverse.  If we're still caught in a death loop then may we just
              # deserve to suffocate! :P
              dx, dy = self.momentum
              dx = dx < 0 and 1 or -1
              dy = dy < 0 and 1 or -1

          self.momentum = (dx, dy)

    if spaced:
      if self.entity == self.engine.player:
        message = 'You drift off into space, never to be seen again...'
      else:
        message = f'{self.entity.name} drifts off into space, never to be seen again...'
      self.engine.message_log.add_message(message)
      self.entity.fighter.die()

    else:
      if gamemap.tiles[self.entity.x + dx, self.entity.y + dy]['tile_class'] == 'floor':
        # We're are drifting on to a floor, resume normal operations after this action
        self.entity.ai = self.parent_ai
      if self.entity == self.engine.player:
        return MovementAction(self.entity, dx, dy)
      else:
        return MovementAction(self.entity, dx, dy).perform()

    return None

  def _is_blocked(self, x, y):
    gamemap = self.entity.parent.gamemap
    if not gamemap.tiles[x, y]['walkable'] or gamemap.get_blocking_entity_at_location(x, y):
      return True
    else:
      return False
