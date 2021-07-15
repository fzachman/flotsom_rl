import color
from components.base_component import BaseComponent
from input_handlers import GameOverEventHandler
from render_order import RenderOrder

class Fighter(BaseComponent):
  def __init__(self, hp, base_defense, base_power, base_accuracy, shields=0):
    self.max_hp = hp
    self._hp = hp
    self.base_defense = base_defense
    self.base_power = base_power
    self.base_accuracy = base_accuracy
    self._shields = shields

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



  def heal(self, amount):
    if self.hp == self.max_hp:
      return 0

    new_hp_value = self.hp + amount
    if new_hp_value > self.max_hp:
      new_hp_value = self.max_hp

    amount_recovered = new_hp_value - self.hp

    self.hp = new_hp_value

    return amount_recovered

  def take_damage(self, amount):
    self.hp -= amount

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
    self.engine.player.level.add_xp(self.parent.level.xp_given)
