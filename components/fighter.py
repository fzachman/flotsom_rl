import color
from components.base_component import BaseComponent
from input_handlers import GameOverEventHandler
from render_order import RenderOrder
from equipment_types import EquipmentType

class Fighter(BaseComponent):
  def __init__(self, hp, base_defense, base_power, base_accuracy, shields=0):
    self.max_hp = hp
    self._hp = hp
    self.base_defense = base_defense
    self.base_power = base_power
    self.base_accuracy = base_accuracy
    self._shields = shields
    self.damaged_by_player = False

  @property
  def hp(self):
    return self._hp

  @hp.setter
  def hp(self, value):
    self._hp = max(0, min(value, self.max_hp))
    if self._hp == 0 and self.parent.ai:
      self.die()

  @property
  def defense(self):
    return self.base_defense + self.defense_bonus

  @property
  def power(self):
    return self.base_power + self.power_bonus

  @property
  def accuracy(self):
    return self.base_accuracy + self.accuracy_bonus

  @property
  def shields(self):
    if self.parent.equipment:
      return self.parent.equipment.total_shields + self._shields
    else:
      return self._shields

  @property
  def defense_bonus(self):
    if self.parent.equipment:
      return self.parent.equipment.defense_bonus
    else:
      return 0

  @property
  def power_bonus(self):
    if self.parent.equipment:
      return self.parent.equipment.power_bonus
    else:
      return 0

  @property
  def accuracy_bonus(self):
    if self.parent.equipment:
      return self.parent.equipment.accuracy_bonus
    else:
      return 0


  def after_melee_damage(self, damage_dealt, target):
    equipment = self.parent.equipment
    if equipment:
      for item_slot in equipment.item_slots:
        if item_slot.item and item_slot.item.equippable.equipment_type in (EquipmentType.MELEE_WEAPON,EquipmentType.ACCESSORY):
          item_slot.item.equippable.after_melee_damage(damage_dealt, target)

  def after_ranged_damage(self, damage_dealt, target):
    equipment = self.parent.equipment
    if equipment:
      for item_slot in equipment.item_slots:
        if item_slot.item and item_slot.item.equippable.equipment_type in (EquipmentType.RANGED_WEAPON,EquipmentType.ACCESSORY):
          item_slot.item.equippable.after_ranged_damage(damage_dealt, target)

  def after_damaged(self, damage_taken, source):
    equipment = self.parent.equipment
    if equipment:
      for item_slot in equipment.item_slots:
        if item_slot.item and item_slot.item.equippable.equipment_type in (EquipmentType.OUTFIT,EquipmentType.ACCESSORY):
          item_slot.item.equippable.after_damaged(damage_taken, source)



  def heal(self, amount):
    if self.hp == self.max_hp:
      return 0

    new_hp_value = self.hp + amount
    if new_hp_value > self.max_hp:
      new_hp_value = self.max_hp

    amount_recovered = new_hp_value - self.hp

    self.hp = new_hp_value

    return amount_recovered

  def take_damage(self, amount, is_player_damage=True, ignores_shields=False):
    amount = amount
    # Apply any damage to shields first, unless this damage ignore shields, like suffocation
    if not ignores_shields:
      if self.parent.equipment:
        for item_slot in self.parent.equipment.item_slots:
          if item_slot.item and item_slot.item.equippable.shields > 0:
            # Each shield item will have a powered component.  One point of power
            # equals one point of shields.  Any extra damage above the shields on this
            # item will be returned.  Apply all of it until we run out of damage or run
            # out of items.
            amount = item_slot.item.equippable.deplete(amount)
          if amount <= 0:
            break
    if amount > 0:
      self.hp -= amount

    if is_player_damage:
      # Don't reward XP for enemies that die solely from the environment
      # or other entities
      self.damaged_by_player = True

  def die(self):
    if self.engine.player is self.parent:
      death_message = 'You died!'
      death_message_color = color.player_die
    else:
      death_message = f'{self.parent.name} is dead!'
      death_message_color = color.enemy_die

    self.parent.char = '%'
    self.parent.color = (191, 0, 0)
    self.parent.blocks_movement = False
    self.parent.ai = None
    self.parent.name = f'remains of {self.parent.name}'
    self.parent.render_order = RenderOrder.CORPSE

    self.engine.message_log.add_message(death_message, death_message_color)
    if self.damaged_by_player:
      # Only reward XP if the player damaged this entity at least once
      self.engine.player.level.add_xp(self.parent.level.xp_given)
