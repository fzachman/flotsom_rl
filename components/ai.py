import random

import numpy as np
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

class BaseAI(Action):
  def perform(self):
    raise NotImplementedError()

  def get_path_to(self, dest_x, dest_y):
    """ Compute and return a path to the target position.
    If there is no valid path, then return an empty list."""

    # Copy the walkable array
    cost = np.array(self.entity.gamemap.tiles['walkable'], dtype=np.int8)

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

class TemporaryAI(BaseAI):
  """Allows an entity to receive a temporary change in AI that lasts
  for a certain number of turns and then expires, restoring their original
  AI"""
  def __init__(self, entity, previous_ai, new_ai, turns_remaining, expire_message=None):
    super().__init__(entity)
    self.previous_ai
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
