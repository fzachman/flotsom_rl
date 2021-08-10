from components.base_component import BaseComponent
import exceptions
import color

class Lungs(BaseComponent):
  def __init__(self, max_o2=20, depletion_time=4):
    self.max_o2 = max_o2
    self.current_o2 = max_o2
    self.depletion_time = depletion_time
    self.breaths = 0

  def breath(self):
    if self.parent.is_alive:
      self.breaths += 1
      if self.breaths >= self.depletion_time:
        self.current_o2 -= 1
        self.breaths = 0

      if self.current_o2 < 0:
        self.current_o2 = 0
        self.parent.fighter.take_damage(1, is_player_damage=False, ignores_shields=True)
        if self.engine.game_map.visible[self.parent.x,self.parent.y]:
          if self.parent == self.engine.player:
            message = f'You are suffocating!'
          else:
            message = f'{self.parent.name} is suffocating!'
          self.engine.message_log.add_message(message,fg=color.red)

  def recharge_o2(self):
    self.current_o2 = self.max_o2
    self.breaths = 0


# Used for mechanicals and other non-breathing entities
class NoLungs(Lungs):
  def breath(self):
    pass

  def recharge_o2(self):
    pass
