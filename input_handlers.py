import tcod.event
import math
import os
import textwrap

import actions
from actions import (Action,
                     BumpAction,
                     PickupAction,
                     WaitAction,
                     ActivateAction)
import color
import exceptions
import ui
import render_functions
from equipment_types import EquipmentType
from components.ai import Drifting

MOVE_KEYS = {
  # Arrow keys.
  tcod.event.K_UP: (0, -1),
  tcod.event.K_DOWN: (0, 1),
  tcod.event.K_LEFT: (-1, 0),
  tcod.event.K_RIGHT: (1, 0),
  tcod.event.K_HOME: (-1, -1),
  tcod.event.K_END: (-1, 1),
  tcod.event.K_PAGEUP: (1, -1),
  tcod.event.K_PAGEDOWN: (1, 1),
  # Numpad keys.
  tcod.event.K_KP_1: (-1, 1),
  tcod.event.K_KP_2: (0, 1),
  tcod.event.K_KP_3: (1, 1),
  tcod.event.K_KP_4: (-1, 0),
  tcod.event.K_KP_6: (1, 0),
  tcod.event.K_KP_7: (-1, -1),
  tcod.event.K_KP_8: (0, -1),
  tcod.event.K_KP_9: (1, -1),
  # Vi keys.
  tcod.event.K_h: (-1, 0),
  tcod.event.K_j: (0, 1),
  tcod.event.K_k: (0, -1),
  tcod.event.K_l: (1, 0),
  tcod.event.K_y: (-1, -1),
  tcod.event.K_u: (1, -1),
  tcod.event.K_b: (-1, 1),
  tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
  tcod.event.K_PERIOD,
  tcod.event.K_KP_5,
  tcod.event.K_CLEAR,
  tcod.event.K_KP_PERIOD
}

CONFIRM_KEYS = {
  tcod.event.K_RETURN,
  tcod.event.K_KP_ENTER,
}

class BaseEventHandler(tcod.event.EventDispatch):
  def handle_events(self, event):
    """Handle an event and return the next active event handler."""
    state = self.dispatch(event)
    if isinstance(state, BaseEventHandler):
      return state
    assert not isinstance(state, Action), f"{self!r} can not handle actions."
    return self

  def on_render(self, console: tcod.Console) -> None:
    raise NotImplementedError()

  def ev_quit(self, event: tcod.event.Quit):
    raise SystemExit()

class PopupMessage(BaseEventHandler):
  """ Display a popup text window."""
  def __init__(self, parent_handler, text):
    self.parent = parent_handler
    self.text = text

  def on_render(self, console):
    """ Render parent and dim result, then print message on top"""
    self.parent.on_render(console)
    console.tiles_rgb['fg'] //= 8
    console.tiles_rgb['bg'] //= 8

    console.print(
      console.width // 2,
      console.height // 2,
      self.text,
      fg=color.white,
      bg=color.black,
      alignment=tcod.CENTER,
    )

  def ev_keydown(self, event):
    """ Any key returns to parent handler """
    return self.parent

class EventHandler(BaseEventHandler):
  def __init__(self, engine):
    self.engine = engine

  def handle_events(self, event):
    """Handle events for input handlers with an engine."""
    if not self.engine.player.is_alive and not isinstance(self, GameOverEventHandler):
      # The player was killed sometime during or after the action.
      return GameOverEventHandler(self.engine)

    action_or_state = self.dispatch(event)
    if isinstance(action_or_state, BaseEventHandler):
      return action_or_state
    if self.handle_action(action_or_state):
      # A valid action was performed.
      if not self.engine.player.is_alive:
        # The player was killed sometime during or after the action.
        return GameOverEventHandler(self.engine)
      elif self.engine.player.level.requires_level_up:
        return LevelUpEventHandler(self.engine)
      return MainGameEventHandler(self.engine)  # Return to the main handler.
    return self

  def handle_action(self, action=None):
    """Handle actions returned from event methods.
    Returns True if the action will advance a turn"""
    if action is None:
      return False

    try:
      action.perform()
    except exceptions.Impossible as exc:
      self.engine.message_log.add_message(exc.args[0], color.impossible)
      return False # Skip enemy turn on exception

    #self.engine.handle_enemy_turns()
    self.engine.update_fov()
    self.engine.update_light_levels()
    self.engine.update_vacuum()
    self.engine.breath()
    self.engine.is_enemy_turn = True
    #self.engine.orbit()
    return True

  def ev_mousemotion(self, event):
    if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
      self.engine.mouse_location = event.tile.x, event.tile.y

  def on_render(self, console):
    self.engine.render(console)

class AskUserEventHandler(EventHandler):
  """Handles user input for actions which require special input"""

  def ev_keydown(self, event):
    """By default any key exits this input handler."""
    # Ignore modifier keys.
    if event.sym in {tcod.event.K_LSHIFT,
                     tcod.event.K_RSHIFT,
                     tcod.event.K_LCTRL,
                     tcod.event.K_RCTRL,
                     tcod.event.K_LALT,
                     tcod.event.K_RALT,
                    }:
      return None
    return self.on_exit()

  def ev_mousebuttondown(self, event):
    return self.on_exit()

  def on_exit(self):
    """ Called when the user is trying to exit or cancel the action.
    By default this returns to the main event handler"""
    return MainGameEventHandler(self.engine)

class CharacterScreenEventHandler(AskUserEventHandler):
  TITLE = 'Character Information'

  def on_render(self, console):
    super().on_render(console)

    if self.engine.player.x <= 30:
      x = 40
    else:
      x = 0

    y = 0

    width = len(self.TITLE) + 4

    console.draw_frame(
        x=x,
        y=y,
        width=width,
        height=9,
        title=self.TITLE,
        clear=True,
        fg=(255, 255, 255),
        bg=(0, 0, 0),
    )

    console.print(
      x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}"
    )
    console.print(
      x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
    )
    console.print(
      x=x + 1,
      y=y + 3,
      string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
    )
    fighter = self.engine.player.fighter
    console.print(
      x=x + 1, y=y + 4, string=f"Melee: {fighter.power} ({fighter.base_power}+{fighter.power_bonus})"
    )
    console.print(
      x=x + 1, y=y + 5, string=f"Ranged: {fighter.accuracy} ({fighter.base_accuracy}+{fighter.accuracy_bonus})"
    )
    console.print(
      x=x + 1, y=y + 6, string=f"Defense: {fighter.defense} ({fighter.base_defense}+{fighter.defense_bonus})"
    )
    console.print(
      x=x + 1, y=y + 7, string=f"Shields: {fighter.shields}"
    )


class LevelUpEventHandler(AskUserEventHandler):
  TITLE = 'Level Up'

  def on_render(self, console):
    super().on_render(console)
    x = 0
    y = 0
    render_functions.draw_window(console, x, y, 40, 9, self.TITLE)

    console.print(x=x + 1, y=1, string="Congratulations! You level up!")
    console.print(x=x + 1, y=2, string="Select an attribute to increase.")

    console.print(
      x=x + 1,
      y=4,
      string=f"a) Vitality (+20 HP, from {self.engine.player.fighter.max_hp})",
    )
    console.print(
      x=x + 1,
      y=5,
      string=f"b) Strength (+1 melee, from {self.engine.player.fighter.base_power})",
    )
    console.print(
      x=x + 1,
      y=6,
      string=f"c) Accuracy (+1 ranged, from {self.engine.player.fighter.base_accuracy})",
    )
    console.print(
      x=x + 1,
      y=7,
      string=f"d) Agility (+1 defense, from {self.engine.player.fighter.base_defense})",
    )


  def ev_keydown(self, event):
    player = self.engine.player
    key = event.sym
    index = key - tcod.event.K_a

    if 0 <= index <= 3:
      if index == 0:
        player.level.increase_max_hp()
      elif index == 1:
        player.level.increase_power()
      elif index == 2:
        player.level.increase_accuracy()
      else:
        player.level.increase_defense()
    else:
      self.engine.message_log.add_message("Invalid entry.", color.invalid)
      return None

    return super().ev_keydown(event)

  def ev_mousebuttondown(self, event):
    """
    Don't allow the player to click to exit the menu, like normal.
    """
    return None

class BasicMenuHandler(AskUserEventHandler):
  TITLE = '<missing title>'
  def __init__(self, engine, options, x=0, y=0, height=None, width=None):
    super().__init__(engine)
    self.options = options
    if not height:
      height = len(self.options) + 2
    if not width:
      width = 20

    if y + height > engine.game_world.viewport_height:
      height = engine.game_world.viewport_height - y

    self.menu = ui.BasicMenu(self.options, x, y, height, width, title=self.TITLE)

  def on_item_selected(self):
    return PopupMessage(MainGameEventHandler(self.engine), self.options[self.menu.cursor])

  def ev_keydown(self, event):
    key = event.sym

    if key in (tcod.event.K_UP, tcod.event.K_KP_8):
      self.menu.up()
      return None
    elif key in (tcod.event.K_DOWN, tcod.event.K_KP_2):
      self.menu.down()
      return None
    elif key in CONFIRM_KEYS:
      return self.on_item_selected()

    elif key == tcod.event.K_ESCAPE:
      return MainGameEventHandler(self.engine)

  def ev_mousemotion(self, event):
    self.menu.mouse_select(event.tile.x, event.tile.y)

  def ev_mousebuttondown(self, event):
    selected = self.menu.mouse_select(event.tile.x, event.tile.y)
    if selected is not None:
      return self.on_item_selected()

  def ev_mousewheel(self, event):
    if event.y > 0:
      self.menu.up()
    elif event.y < 0:
      self.menu.down()

  def on_render(self, console):
    super().on_render(console)
    self.menu.render(console)

class InventoryEventHandler(BasicMenuHandler):
  """ This handler lets the user select an item.
  What happens then depends on the subclass."""
  TITLE = '<missing title>'

  def __init__(self, engine, filter_function=lambda x: True):
    self.filter_function = filter_function
    self.filtered_items = []
    for item in engine.player.inventory.items:
      if self.filter_function(item):
        self.filtered_items.append(item)
    self.options = options = []

    min_width = len(self.TITLE) + 6
    for i in self.filtered_items:
      is_equipped = engine.player.equipment.item_is_equipped(i)
      item_name = i.name
      if is_equipped:
        item_name += ' (E)'
      options.append(item_name)
      if len(item_name) > min_width:
        min_width = len(item_name)

    super().__init__(engine, options, width=min_width + 2)

  def on_render(self, console):
    super().on_render(console)

  #def ev_keydown(self, event):
  #  player = self.engine.player
  #  key = event.sym
  #  index = key - tcod.event.K_a

  #  if 0 <= index <= 26:
  #    # Did they push a letter between a and z
  #    try:
  #      selected_item = self.filtered_items[index]#player.inventory.items[index]
  #    except IndexError:
  #      self.engine.message_log.add_message('Invalid entry.', color.invalid)
  #      return None
  #    return self.on_item_selected(selected_item)
  #  return super().ev_keydown(event)

  def on_item_selected(self, item):
    """Called when the user selectes a valid item."""
    raise NotImplementedError()

class InventoryActivateHandler(InventoryEventHandler):
  """Handle using an inventory item."""

  TITLE = 'Select an item to use'

  def on_item_selected(self):#, item):
    """Return the action for the selected item"""
    item = self.filtered_items[self.menu.cursor]
    if item.consumable:
      return item.consumable.get_action(self.engine.player)
    elif item.equippable:
      return actions.EquipAction(self.engine.player, item)
    else:
      return None

class InventoryRechargeHandler(InventoryEventHandler):
  """Handle energizing an inventory item."""

  TITLE = 'Recharge:'
  def __init__(self, engine, battery):
    def filter_powered(item):
      if item.powered:
        return True
      else:
        return False

    super().__init__(engine, filter_powered)
    self.battery = battery

  def on_item_selected(self):#, item):
    """Return the action for the selected item"""
    item = self.filtered_items[self.menu.cursor]
    return actions.RechargeAction(self.engine.player, self.battery, item)

class InventoryDropHandler(InventoryEventHandler):
  """Handle dropping an inventory item"""

  TITLE = 'Select and item to drop'

  def on_item_selected(self):#, item):
    item = self.filtered_items[self.menu.cursor]
    return actions.DropItem(self.engine.player, item)

class SelectIndexHandler(AskUserEventHandler):
  """Handles asking the user for an index on the map"""
  def __init__(self, engine):
    """Sets the curor to the player when this handler is constructed"""
    super().__init__(engine)
    player = self.engine.player
    viewport = self.engine.game_map.get_viewport()
    engine.mouse_location = player.x - viewport[0], player.y-viewport[1]

  def on_render(self, console):
    """Highlight the tile under the cursor"""
    super().on_render(console)
    x, y = self.engine.mouse_location

    console.tiles_rgb['bg'][x,y] = color.white
    console.tiles_rgb['fg'][x,y] = color.black

  def ev_keydown(self, event):
    """Check for movement or confirmation keys"""
    key = event.sym
    if key in MOVE_KEYS:
      modifier = 1 # Holding modifier keys will speed up key movement
      if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
        modifier *= 5
      if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
        modifier *= 10
      if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
        modifier *= 20

      x, y = self.engine.mouse_location
      dx, dy = MOVE_KEYS[key]
      x += dx * modifier
      y += dy * modifier
      # Clamp the cursor index to map size
      x = max(0, min(x, self.engine.game_map.width -1))
      y = max(0, min(y, self.engine.game_map.height -1))
      self.engine.mouse_location = x,y
      return None
    elif key in CONFIRM_KEYS:
      return self.on_index_selected(*self.engine.mouse_location)

    return super().ev_keydown(event)

  def ev_mousebuttondown(self, event):
    """Left click confirms a selection"""
    if self.engine.game_map.in_bounds(*event.tile):
      if event.button == 1:
        viewport = self.engine.game_map.get_viewport()
        x = event.tile.x + viewport[0]
        y = event.tile.y + viewport[1]
        return self.on_index_selected(x,y)
    return super().ev_mousebuttondown(event)

  def on_index_selected(self, x, y):
    """Called when an index is selected"""
    raise NotImplementedError()

class LookHandler(SelectIndexHandler):
  """ Lets the player look around using the keyboard """
  def on_index_selected(self, x, y):
    """Return to main handler"""
    return MainGameEventHandler(self.engine)

class SingleRangedAttackHandler(SelectIndexHandler):
  """ Handles targeting a single enemy.  Only the enemy selected will be affected. """
  def __init__(self, engine, callback = None):
    super().__init__(engine)
    self.callback = callback

  def on_index_selected(self, x, y):
    v_x, v_y, v_x1, v_y1 = self.engine.game_map.get_viewport()
    x+= v_x
    y += v_y
    return self.callback((x, y))

class AreaRangedAttackHandler(SelectIndexHandler):
  """Handles targeting an area within a given radius.  Any entity in the area
  will be affected"""

  def __init__(self, engine, radius, callback):
    super().__init__(engine)
    self.radius = radius
    self.callback = callback

  def on_render(self, console):
    """Highlight the tile under the cursor"""
    super().on_render(console)
    viewport = self.engine.game_map.get_viewport()
    x, y = self.engine.mouse_location
    #print(f'Origin ({x}, {y})')
    for tx in range(x-self.radius, x+self.radius+1):
      for ty in range(y-self.radius, y+self.radius+1):
        if math.sqrt((x - tx) ** 2 + (y - ty) **2) <= self.radius and \
              self.engine.game_map.in_bounds(tx+viewport[0], ty+viewport[1]) and \
              self.engine.game_map.visible[(tx+viewport[0],ty+viewport[1])]:

          #print(f'AOE Tile ({tx}, {ty})')
          console.tiles_rgb['bg'][tx,ty] = color.white
          console.tiles_rgb['fg'][tx,ty] = color.black

    # Draw a rectangle around the targeted area so the player can ese the affected tiles
    #console.draw_frame(
    #  x=x - self.radius - 1,
    #  y=y - self.radius - 1,
    #  width = self.radius ** 2,
    #  height = self.radius ** 2,
    #  fg=color.red,
    #  clear=False,
    #)

  def on_index_selected(self, x, y):
    return self.callback((x,y))

class MainGameEventHandler(EventHandler):
  def ev_keydown(self, event: tcod.event.KeyDown):
    action = None

    key = event.sym
    modifier = event.mod

    player = self.engine.player
    if isinstance(player.ai, Drifting):
      return player.ai.perform()

    if key == tcod.event.K_PERIOD and modifier & (
      tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
    ):
      return actions.TakeEscapePodAction(player)

    if key in MOVE_KEYS:
      dx, dy = MOVE_KEYS[key]
      action = BumpAction(player, dx, dy)
    elif key in WAIT_KEYS:
      action = WaitAction(player)

    elif key == tcod.event.K_s:
      ranged_weapon = player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON)
      if not ranged_weapon:
        self.engine.message_log.add_message('You do not have a ranged weapon equipped!')
      elif not ranged_weapon.equippable.is_energized:
        self.engine.message_log.add_message('That item is depleted.  Recharge it with an energy cell before using!')
      else:
        self.engine.message_log.add_message('Select a target.', color.needs_target)
        return SingleRangedAttackHandler(
                  self.engine,
                  callback=lambda xy: actions.TargetedRangedAttack(player, xy),
                )

    elif key in (tcod.event.K_ESCAPE, tcod.event.K_q):
      raise SystemExit()
    elif key == tcod.event.K_v:
      return HistoryViewer(self.engine)
    elif key == tcod.event.K_g:
      action = PickupAction(player)

    elif key == tcod.event.K_SPACE:
      action = ActivateAction(player)

    elif key == tcod.event.K_m:
      self.engine.game_map.reveal_map()
      return self

    elif key == tcod.event.K_i:
      return InventoryActivateHandler(self.engine)
    elif key == tcod.event.K_d:
      return InventoryDropHandler(self.engine)
    elif key == tcod.event.K_c:
      return CharacterScreenEventHandler(self.engine)
    elif key == tcod.event.K_SLASH:
      if modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
        self.engine.game_map.show_debug = not self.engine.game_map.show_debug
      else:
        return LookHandler(self.engine)

    elif key == tcod.event.K_RETURN:
      return BasicMenuHandler(self.engine)


    return action

  #def ev_mousemotion(self, event):
  #  print(f'Mouse tile location ({event.tile.x}, {event.tile.y})')
  #  print(f'Player tile location ({self.engine.player.x}, {self.engine.player.y})')
  #  x1,y1,x2,y2 = self.engine.game_map.get_viewport()
  #  print(f'Viewport offset ({x1},{y1})')

class GameOverEventHandler(EventHandler):
  def on_quit(self):
    """Handle exiting out of a finished game."""
    if os.path.exists('savegame.sav'):
      os.remove('savegame.sav')
    raise exceptions.QuitWithoutSaving()

  def ev_keydown(self, event):
    key = event.sym
    if key == tcod.event.K_q:
      self.on_quit()

    return None

  def on_render(self, console):
    """ Render parent and dim result, then print message on top"""
    #super().on_render(console)
    console.tiles_rgb['fg'] //= 8
    console.tiles_rgb['bg'] //= 8

    popup_width = 30
    message = 'You have died.  Press Q to quit.'
    lines = textwrap.wrap(message, popup_width - 2)

    popup_height = len(lines) + 2
    x = (console.width // 2) - (popup_width // 2)
    y = (console.height // 2) - (popup_height // 2)
    render_functions.draw_window(console, x, y, popup_width, popup_height, '')
    for i, line in enumerate(lines, start=1):
      console.print(
        console.width // 2,
        y + i,
        line,
        fg=color.white,
        bg=color.black,
        alignment=tcod.CENTER,
      )

CURSOR_Y_KEYS = {
  tcod.event.K_UP: -1,
  tcod.event.K_DOWN: 1,
  tcod.event.K_PAGEUP: -10,
  tcod.event.K_PAGEDOWN: 10,
}

class HistoryViewer(EventHandler):
  """Print the history on a larger window which can be navigated."""

  def __init__(self, engine):
    super().__init__(engine)
    self.log_length = len(engine.message_log.messages)
    self.cursor = self.log_length - 1

  def on_render(self, console):
    super().on_render(console)  # Draw the main state as the background.

    log_console = tcod.Console(console.width-6, console.height-6, order="F")

    # Draw a frame with a custom banner title.
    render_functions.draw_window(log_console, 0, 0, log_console.width-1, log_console.height-1, 'Message History')

    # Render the message log using the cursor parameter.
    self.engine.message_log.render_messages(
        log_console,
        1,
        1,
        log_console.width - 3,
        log_console.height - 3,
        self.engine.message_log.messages[: self.cursor + 1],
    )
    log_console.blit(console, 3, 3)

  def ev_keydown(self, event):
    # Fancy conditional movement to make it feel right.
    if event.sym in CURSOR_Y_KEYS:
        adjust = CURSOR_Y_KEYS[event.sym]
        if adjust < 0 and self.cursor == 0:
            # Only move from the top to the bottom when you're on the edge.
            self.cursor = self.log_length - 1
        elif adjust > 0 and self.cursor == self.log_length - 1:
            # Same with bottom to top movement.
            self.cursor = 0
        else:
            # Otherwise move while staying clamped to the bounds of the history log.
            self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
    elif event.sym == tcod.event.K_HOME:
        self.cursor = 0  # Move directly to the top message.
    elif event.sym == tcod.event.K_END:
        self.cursor = self.log_length - 1  # Move directly to the last message.
    else:  # Any other key moves back to the main game state.
        return MainGameEventHandler(self.engine)

    return None
