import color
import exceptions
import tile_types

class Action:
  def __init__(self, entity):
    super().__init__()
    self.entity = entity

  @property
  def engine(self):
    """ return the engine this action belongs to """
    return self.entity.gamemap.engine

  def perform(self):
    """Perform this action with the objects needed to determine its scope.

    `self.engine` is the scope this action is being performed in.

    `self.entity` is the object performing the action.

    This method must be overridden by Action subclasses.
    """
    raise NotImplementedError()

class PickupAction(Action):
  """Pick up an item and add it to the inventory, if there is room for it."""
  def __init__(self, entity):
    super().__init__(entity)

  def perform(self):
    actor_location_x = self.entity.x
    actor_location_y = self.entity.y
    inventory = self.entity.inventory

    for item in self.engine.game_map.items:
      if actor_location_x == item.x and actor_location_y == item.y:
        if len(inventory.items) >= inventory.capacity:
          raise exceptions.Impossible('Your inventory is full.')
        self.engine.game_map.entities.remove(item)
        item.parent = self.entity.inventory
        inventory.items.append(item)

        self.engine.message_log.add_message(f'You picked up the {item.name}!')
        return

    raise exceptions.Impossible('There is nothing here to pick up.')


class ItemAction(Action):
  def __init__(self, entity, item, target_xy=None):
    super().__init__(entity)
    self.item = item
    if not target_xy:
      target_xy = entity.x, entity.y
    self.target_xy = target_xy

  @property
  def target_actor(self):
    """Return the actor at this actions destination"""
    return self.engine.game_map.get_actor_at_location(*self.target_xy)

  def perform(self):
    """Invoke this items ability, this action will be given to provide context"""
    if self.item.consumable:
      self.item.consumable.activate(self)

class DropItem(ItemAction):
  def perform(self):
    if self.entity.equipment.item_is_equipped(self.item):
      self.entity.equipment.toggle_equip(self.item)

    self.entity.inventory.drop(self.item)

class EquipAction(Action):
  def __init__(self, entity, item):
    super().__init__(entity)
    self.item = item

  def perform(self):
    self.entity.equipment.toggle_equip(self.item)

class EnergizeAction(Action):
  def __init__(self, entity, energizer, item):
    super().__init__(entity)
    self.energizer = energizer
    self.item = item

  def perform(self):
    if self.item.equippable:
      self.item.equippable.energize(self.energizer)
    else:
      raise exceptions.Impossible('You cannot charge that item.')

class WaitAction(Action):
  def perform(self):
    pass

class TakeStairsAction(Action):
  def perform(self):
    if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
      self.engine.game_world.generate_floor()
      self.engine.message_log.add_message('You descend the staircase.', color.descend)
    else:
      raise exceptions.Impossible('There are no stairs here.')

class ActionWithDirection(Action):
  def __init__(self, entity, dx, dy):
    super().__init__(entity)
    self.dx = dx
    self.dy = dy

  @property
  def dest_xy(self):
    return self.entity.x + self.dx, self.entity.y + self.dy

  @property
  def blocking_entity(self):
    return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

  @property
  def target_actor(self):
    return self.engine.game_map.get_actor_at_location(*self.dest_xy)

  def perform(self):
    raise NotImplementedError()

class MeleeAction(ActionWithDirection):
  def perform(self):
    target = self.target_actor
    if not target:
      raise exceptions.Impossible('Nothing to attack.')

    damage = self.entity.fighter.power - target.fighter.defense
    attack_desc = f'{self.entity.name.capitalize()} attacks {target.name}'
    if self.entity is self.engine.player:
      attack_color = color.player_atk
    else:
      attack_color = color.enemy_atk
    if damage > 0:
      self.engine.message_log.add_message(f'{attack_desc} for {damage} hit points.', attack_color)
      target.fighter.hp -= damage
    else:
      self.engine.message_log.add_message(f'{attack_desc} but does no damage.', attack_color)


class MovementAction(ActionWithDirection):
  def perform(self):
    dest_x, dest_y = self.dest_xy

    if not self.engine.game_map.in_bounds(dest_x, dest_y):
      # Destination is out of bounds.
      raise exceptions.Impossible('That way is blocked.')
    #if self.engine.game_map.tiles[dest_x, dest_y] == tile_types.door_closed:
    if self.engine.game_map.tile_set.is_tile_class(self.engine.game_map.tiles[dest_x, dest_y], 'door', 'closed'):
      self.engine.game_map.tiles[dest_x, dest_y] = self.engine.game_map.tile_set.get_tile_type('door','open')#tile_types.door_open
      return
    if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
      # Destination is blocked by a tile.
      raise exceptions.Impossible('That way is blocked.')
    if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
      # Destination blocked by an enemy
      raise exceptions.Impossible('That way is blocked.')

    self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
  def perform(self):
    if self.target_actor:
      return MeleeAction(self.entity, self.dx, self.dy).perform()
    else:
      return MovementAction(self.entity, self.dx, self.dy).perform()


class TargetedRangedAttack(Action):
  def __init__(self, entity, target):
    super().__init__(self)
    self.target = target

  def perform(self):
    pass
