from components.base_component import BaseComponent
from equipment_types import EquipmentType
from exceptions import Impossible

class ItemSlot:
  def __init__(self, equipment_type, slot_name, item=None):
    self.equipment_type = equipment_type
    self.slot_name = slot_name
    self.item = item

class Equipment(BaseComponent):
  def __init__(self):
    self.item_slots = [
      ItemSlot(EquipmentType.MELEE_WEAPON, 'Melee Weapon'),
      ItemSlot(EquipmentType.RANGED_WEAPON, 'Ranged Weapon'),
      ItemSlot(EquipmentType.OUTFIT, 'Outfit'),
      ItemSlot(EquipmentType.ACCESSORY, 'Accessory'),
    ]

  @property
  def defense_bonus(self):
    bonus = 0
    for item_slot in self.item_slots:
      if item_slot.item:
        bonus += item_slot.item.equippable.defense_bonus
    return bonus

  @property
  def power_bonus(self):
    bonus = 0
    for item_slot in self.item_slots:
      if item_slot.item:
        bonus += item_slot.item.equippable.power_bonus
    return bonus

  @property
  def accuracy_bonus(self):
    bonus = 0
    for item_slot in self.item_slots:
      if item_slot.item:
        bonus += item_slot.item.equippable.accuracy_bonus
    return bonus


  @property
  def current_shields(self):
    total_shields = 0
    for item_slot in self.item_slots:
      if item_slot.item and item_slot.item.equippable.provides_shields and item_slot.item.powered:
        total_shields += item_slot.item.powered.current_power
    return total_shields

  @property
  def max_shields(self):
    total_shields = 0
    for item_slot in self.item_slots:
      if item_slot.item and item_slot.item.equippable.provides_shields and item_slot.item.powered:
        total_shields += item_slot.item.powered.max_power
    return total_shields

  def has_item_in_slot(self, equipment_type):
    for s in self.item_slots:
      if s.equipment_type == equipment_type and s.item is not None:
        return True
    return False

  def get_item_in_slot(self, equipment_type):
    for s in self.item_slots:
      if s.equipment_type == equipment_type and s.item is not None:
        return s.item
    return None

  def item_is_equipped(self, item):
    for item_slot in self.item_slots:
      if item_slot.item == item:
        return True
    return False

  def unequip_message(self, item_name):
    self.parent.gamemap.engine.message_log.add_message(f'You unequip the {item_name}.')

  def equip_message(self, item_name):
    self.parent.gamemap.engine.message_log.add_message(f'You equip the {item_name}.')

  def equip(self, item, add_message):

    for item_slot in self.item_slots:
      if item_slot.equipment_type == item.equippable.equipment_type:
        if item_slot.item:
          self.unequip(item_slot.equipment_type, add_message)
        item_slot.item = item
        if add_message:
          self.equip_message(item.name)

  def unequip(self, equipment_type, add_message):
    for item_slot in self.item_slots:
      if item_slot.equipment_type == equipment_type:
        if add_message:
          self.unequip_message(item_slot.item.name)
        item_slot.item = None
        break

  def toggle_equip(self, equippable_item, add_message=True):
    for item_slot in self.item_slots:
      if item_slot.equipment_type == equippable_item.equippable.equipment_type:
        if item_slot.item == equippable_item:
          self.unequip(equippable_item.equippable.equipment_type, add_message)
        else:
          self.equip(equippable_item, add_message)
        break
