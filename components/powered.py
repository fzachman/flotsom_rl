from components.base_component import BaseComponent
from equipment_types import EquipmentType
import exceptions
import color

class Powered(BaseComponent):
  def __init__(self, max_power, efficiency=1):
    self.max_power = max_power
    self.current_power = max_power
    self.efficiency = efficiency

  @property
  def powered(self):
    return self.current_power > 0

  def recharge(self, battery):
    if self.current_power >= self.max_power:
      raise exceptions.Impossible('That item is already at maximum charge.')

    recharged = battery.amount * self.efficiency
    self.current_power += recharged
    if self.current_power > self.max_power:
      recharged -= self.current_power - self.max_power
      self.current_power = self.max_power

    self.engine.message_log.add_message(f'{recharged} power is restored to {self.parent.name}')

    battery.consume()

  def deplete(self, amount=1):
    over_depletion = 0
    if self.current_power > 0:
      self.current_power -= amount
      if self.current_power < 0:
        overdepletion = abs(self.current_power)
        self.current_power = 0
    if self.current_power == 0:
      # Uh.....
      self.engine.message_log.add_message(f'{self.parent.name} has run out of power!', fg=color.warning)
    return over_depletion
