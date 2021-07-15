from components.base_component import BaseComponent

class Level(BaseComponent):
  def __init__(self, current_level=1,
               current_xp = 0,
               level_up_base = 0,
               level_up_factor = 150,
               xp_given=0):
    self.current_level = current_level
    self.current_xp = current_xp
    self.level_up_base = level_up_base
    self.level_up_factor = level_up_factor
    self.xp_given = xp_given

  @property
  def experience_to_next_level(self):
    return self.level_up_base + self.current_level * self.level_up_factor

  @property
  def requires_level_up(self):
    return self.current_xp > self.experience_to_next_level

  def add_xp(self, xp):
    if xp == 0 or self.level_up_base == 0:
      return

    self.current_xp += xp
    self.engine.message_log.add_message(f'You earn {xp} experience points.')

    if self.requires_level_up:
      self.engine.message_log.add_message(f'You advance to level {self.current_level + 1}!')

  def increase_level(self):
    self.current_xp -= self.experience_to_next_level
    self.current_level += 1

  def increase_max_hp(self, amount = 20):
    self.parent.fighter.max_hp += amount
    self.parent.fighter.hp += amount
    self.engine.message_log.add_message('Your health improves!')
    self.increase_level()

  def increase_power(self, amount=1):
    self.parent.fighter.base_power += amount
    self.engine.message_log.add_message("You feel stronger!")
    self.increase_level()

  def increase_defense(self, amount: int = 1) -> None:
    self.parent.fighter.base_defense += amount
    self.engine.message_log.add_message("Your movements are getting swifter!")
    self.increase_level()

  def increase_accuracy(self, amount: int = 1) -> None:
    self.parent.fighter.base_accuracy += amount
    self.engine.message_log.add_message("Your aim improves!")
    self.increase_level()
