from enum import Enum, auto
import random
import color
import animations

class Effect:
  def __init__(self, level):
    self.level = level

  def trigger(self, triggerer, damage, target):
    """ triggerer is the acting entity, target is being acted upon.  For melee/ranged
    damage trigers, the acting entity will be the entity doing the damage and the target
    will be taking the damage.  For on_damaged triggers, this will be the opposite: triggerer
    will be the entity that damaged the target """
    raise NotImplementedError

class Knockback(Effect):
  """ Knocks an entity back after being hit """
  def __init__(self, level):
    super().__init__(level)
    self.distance = distance = 1
    modifier = random.randint(1,20)
    if modifier + level >= 19:
      self.distance = 2
    elif modifier + level >= 29:
      self.distance = 3
    elif modifier + level >= 39:
      self.distance = 4

  def trigger(self, triggerer, damage, target):
    #dx = triggerer.x - target.x
    #dy = triggerer.y - target.y

    mx = 0
    my = 0
    if target.x < triggerer.x:
      mx = -1
    elif target.x > triggerer.x:
      mx = 1
    if target.y < triggerer.y:
      my = -1
    elif target.y > triggerer.y:
      my = 1

    game_map = triggerer.gamemap
    for i in range(self.distance):
      new_x = target.x + mx
      new_y = target.y + my
      #print(f'Knockback({self.distance}) Source {triggerer}@({triggerer.x},{triggerer.y}), target: ({target.x},{target.y}), moving to: ({new_x},{new_y})')
      if game_map.in_bounds(new_x, new_y) and \
         game_map.tiles[new_x, new_y]['walkable'] and \
         not game_map.get_blocking_entity_at_location(new_x, new_y):
        target.move(mx, my)
      else:
        # Once we hit something: wall/entity/edge of map, stop pushing
        break
    game_map.engine.message_log.add_message(f'{target.name} is thrown back!', fg=color.status_effect_applied)

class ChainLightning(Effect):
  """ Does Damage to all entities around the target """
  def __init__(self, level):
    super().__init__(level)
    self.damage = 1
    modifier = random.randint(1,20)
    if modifier + level >= 16:
      self.damage = 2
    elif modifier + level >= 21:
      self.damage = 3
    elif modifier + level >= 26:
      self.damage = 4
    elif modifier + level >= 31:
      self.damage = 5


  def trigger(self, triggerer, damage, target):
    for dx,dy in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
      x = target.x + dx
      y = target.y + dy
      actor = triggerer.gamemap.get_actor_at_location(x, y)
      if actor and actor != triggerer and actor.fighter:
        triggerer.gamemap.engine.message_log.add_message(f'Electricity leaps to {actor.name}, striking it for {self.damage} damage!',
                                                          fg=color.status_effect_applied, stack=False)
        actor.fighter.take_damage(self.damage)
        triggerer.gamemap.engine.queue_animation(animations.DamagedAnimation(actor, color.damage_electric))


on_melee_damage_triggers = (Knockback, ChainLightning)
on_range_damage_triggers = (Knockback, ChainLightning)
on_damaged_triggers = (Knockback)
