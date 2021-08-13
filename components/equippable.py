from components.base_component import BaseComponent
from equipment_types import EquipmentType
import exceptions
import color

class Equippable(BaseComponent):

  def __init__(self, equipment_type,
                     power_bonus=0,
                     defense_bonus=0,
                     accuracy_bonus=0,
                     provides_shields=False):
    """If the parent item also has a 'powered' component, using this item may
    deplete the power.  If this item provides shields, it provides shields equal
    to it's 'powered' components current power."""
    self.equipment_type = equipment_type
    self._power_bonus = power_bonus
    self._defense_bonus = defense_bonus
    self._accuracy_bonus = accuracy_bonus
    self.provides_shields = provides_shields

    self._after_melee_damage_effects = []
    self._after_ranged_damage_effects = []
    self._after_damaged_effects = []

  @property
  def is_energized(self):
    if self.parent.powered is None or self.parent.powered.current_power > 0:
      return True
    return False

  @property
  def power_bonus(self):
    if self.is_energized:
      return self._power_bonus
    else:
      return 0

  @property
  def defense_bonus(self):
    if self.is_energized:
      return self._defense_bonus
    else:
      return 0

  @property
  def accuracy_bonus(self):
    if self.is_energized:
      return self._accuracy_bonus
    else:
      return 0

  @property
  def shields(self):
    if self.provides_shields and self.parent.powered:
      return self.parent.powered.current_power
    else:
      return 0

  @property
  def max_shields(self):
    if self.provides_shields and self.parent.powered:
      return self.parent.powered.max_power
    else:
      return 0

  def deplete(self, amount=1):
    if self.parent.powered:
      over_depletion = self.parent.powered.deplete(amount)
    return over_depletion

  def add_after_melee_damage_effect(self, effect):
    """ Add a component that triggers after doing melee damage."""
    self._after_melee_damage_effects.append(effect)

  def add_after_ranged_damage_effect(self, effect):
    """ Add a component that triggers after doing ranged damage."""
    self._after_ranged_damage_effects.append(effect)

  def add_after_damaged_effect(self, effect):
    """ Add a component that triggers after doing taking damage."""
    self._after_damaged_effects.append(effect)

  def after_melee_damage(self, damage_dealt, target=None):
    for effect in self._after_melee_damage_effects:
      if self.is_energized:
        effect.trigger(self.parent.parent.parent, damage_dealt, target)
        self.deplete()

  def after_ranged_damage(self, damage_dealt, target=None):
    for effect in self._after_ranged_damage_effects:
      if self.is_energized:
        effect.trigger(self.parent.parent.parent, damage_dealt, target)
        self.deplete()


  def after_damaged(self, damage_taken, source=None):
    for effect in self._after_damaged_effects:
      if self.is_energized:
        effect.trigger(source, damage_taken, self.parent.parent.parent)
        self.deplete()

class Knife(Equippable):
  def __init__(self):
    super().__init__(equipment_type=EquipmentType.MELEE_WEAPON, power_bonus=2)

class PowerFist(Equippable):
  def __init__(self):
    super().__init__(equipment_type=EquipmentType.MELEE_WEAPON, power_bonus=4)

class Gun(Equippable):
  def __init__(self):
    super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, accuracy_bonus=1)

class SpacersSuit(Equippable):
  def __init__(self):
    super().__init__(equipment_type=EquipmentType.OUTFIT, defense_bonus=1)

class ArmoredSpacersSuit(Equippable):
  def __init__(self):
    super().__init__(equipment_type=EquipmentType.OUTFIT, defense_bonus=3)

class ShieldBelt(Equippable):
  def __init__(self):
    super().__init__(equipment_type=EquipmentType.ACCESSORY, provides_shields=True)
