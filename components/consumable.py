import actions
import color
import components.ai
import components.inventory
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import AreaRangedAttackHandler, SingleRangedAttackHandler, InventoryEnergizeHandler

class Consumable(BaseComponent):
  def get_action(self, consumer):
    """ Try to return the action for this item."""
    return actions.ItemAction(consumer, self.parent)

  def activate(self, action):
    """ Invoke this items abililty

    `action` is the context for this activation"""
    raise NotImplementedError

  def consume(self):
    """ Remove the consumed item from its containing inventory"""
    entity = self.parent
    inventory = entity.parent
    if isinstance(inventory, components.inventory.Inventory):
      inventory.items.remove(entity)

class ConfusionConsumable(Consumable):
  def __init__(self, number_of_turns):
    self.number_of_turns = number_of_turns

  def get_action(self, consumer):
    self.engine.message_log.add_message('Select a target location.', color.needs_target)
    return SingleRangedAttackHandler(
              self.engine,
              callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
            )

  def activate(self, action):
    consumer = action.entity
    target = action.target_actor

    if not self.engine.game_map.visible[action.target_xy]:
      raise Impossible('You cannot target an area that you cannot see.')
    if not target:
      raise Impossible('You must select an enemy to target.')
    if target is consumer:
      raise Impossible('You cannot hit yourself!')

    self.engine.message_log.add_message(
      f'Confused, the {target.name} begins to stumble around!',
      color.status_effect_applied,
    )
    new_ai = components.ai.ConfusedEnemey(entity=target)

    target.ai = components.ai.TemporaryAI(
      entity=target,
      previous_ai = target.ai,
      new_ai = new_ai,
      turns_remaining = self.number_of_turns,
      expire_message=f'The {target.name} is no longer confused.'
    )

    self.consume()

class HealingConsumable(Consumable):
  def __init__(self, amount):
    self.amount = amount

  def activate(self, action):
    consumer = action.entity
    amount_recovered = consumer.fighter.heal(self.amount)

    if amount_recovered > 0:
      self.engine.message_log.add_message(
        f'You slap the {self.parent.name} on yourself and recover {amount_recovered} HP!',
        color.health_recovered
      )
      self.consume()
    else:
      raise Impossible('Your health is already at full.')

class FireballDamageConsumable(Consumable):
  def __init__(self, damage, radius):
    self.damage = damage
    self.radius = radius

  def get_action(self, consumer):
    self.engine.message_log.add_message('Select a target location.', color.needs_target)
    return AreaRangedAttackHandler(self.engine,
                                   radius=self.radius,
                                   callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
                                  )

  def activate(self, action):
    target_xy = action.target_xy
    if not self.engine.game_map.visible[target_xy]:
      raise Impossible('You cannot target an area that you cannot see.')

    targets_hit = False
    for actor in self.engine.game_map.actors:
      if actor.distance(*target_xy) <= self.radius:
        self.engine.message_log.add_message(f'The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!')
        actor.fighter.take_damage(self.damage)
        targets_hit = True

    if not targets_hit:
      raise Impossible("There are no targets in the radius.")
    self.consume()

class EnergyConsumable(Consumable):
  def __init__(self, amount):
    self.amount = amount

  def get_action(self, consumer):
    return InventoryEnergizeHandler(self.engine, self)

  def activate(self, action):
    return InventoryEnergizeHandler(self.engine, self)

class LightningDamageConsumable(Consumable):
  def __init__(self, damage, maximum_range):
    self.damage = damage
    self.maximum_range = maximum_range

  def activate(self, action):
    consumer = action.entity
    target = None
    closest_distance = self.maximum_range + 1.0

    for actor in self.engine.game_map.actors:
      if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
        distance = consumer.distance(actor.x, actor.y)
        if distance < closest_distance:
          target = actor
          closest_distance = distance

    if target:
      self.engine.message_log.add_message(f'A beam of light strikes the {target.name} with searing intensity for {self.damage} damage!')
      target.fighter.take_damage(self.damage)
      self.consume()
    else:
      raise Impossible('No enemy is close enough to strike.')
