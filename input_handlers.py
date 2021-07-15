import tcod.event
import math
import os

import actions
from actions import (Action,
                     BumpAction,
                     PickupAction,
                     WaitAction,)
import color
import exceptions

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

    self.engine.handle_enemy_turns()
    self.engine.update_fov()
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

    if self.engine.player.x <= 30:
      x = 40
    else:
      x = 0

    console.draw_frame(
          x=x,
          y=0,
          width=35,
          height=8,
          title=self.TITLE,
          clear=True,
          fg=(255, 255, 255),
          bg=(0, 0, 0),
      )

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
      string=f"d) Accuracy (+1 ranged, from {self.engine.player.fighter.base_accuracy})",
    )
    console.print(
      x=x + 1,
      y=7,
      string=f"c) Agility (+1 defense, from {self.engine.player.fighter.base_defense})",
    )


  def ev_keydown(self, event):
    player = self.engine.player
    key = event.sym
    index = key - tcod.event.K_a

    if 0 <= index <= 2:
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

class InventoryEventHandler(AskUserEventHandler):
  """ This handler lets the user select an item.
  What happens then depends on the subclass."""
  TITLE = '<missing title>'

  def on_render(self, console):
    """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
    Will move to a different position based on where the player is located, so the player can always see where
    they are.
    """
    super().on_render(console)
    number_of_items_in_inventory = len(self.engine.player.inventory.items)

    height = self.engine.game_world.viewport_height#number_of_items_in_inventory + 2


    #if height <= 3:
    #  height = 3

    #if self.engine.player.x <= 30:
    #  x = 40
    #else:
    #  x = 0
    x = 0
    y = 0

    #width = len(self.TITLE) + 4
    #if number_of_items_in_inventory > 0:
    #  for i, item in enumerate(self.engine.player.inventory.items):
    #    if len(item.name) + 10 > width:
    #      width = len(item.name) + 10

    width = int(self.engine.game_world.viewport_width / 3)

    console.draw_frame(x = x,
                       y = y,
                       width=width,
                       height=height,
                       title=self.TITLE,
                       clear=True,
                       fg=(255,255,255),
                       bg=(0,0,0))

    if number_of_items_in_inventory > 0:
      for i, item in enumerate(self.engine.player.inventory.items):
        item_key = chr(ord('a') + i)
        is_equipped = self.engine.player.equipment.item_is_equipped(item)
        item_string = f'({item_key}) {item.name}'
        if is_equipped:
          item_string = f'{item_string} (E)'

        console.print(x + 1, y + i + 1, item_string)
    else:
      console.print(x + 1, y+1, '(Empty)')

    console.draw_frame(x=x+width,
                       y=y,
                       width=width,
                       height=height,
                       title="Current Equipment",
                       clear=True,
                       fg=(255,255,255),
                       bg=(0,0,0))
    equip_y = y + 2
    equip_x = x + width + 1
    for slot in self.engine.player.equipment.item_slots:
      if slot.item:
        console.print(equip_x, equip_y, slot.slot_name)
        item_name = f'-{slot.item.name}'
        if slot.item.equippable.max_energy_level > 0:
          item_name = f'{item_name} ({slot.item.equippable.current_energy_level}/{slot.item.equippable.max_energy_level})'
        console.print(equip_x, equip_y + 1, item_name)
        equip_y += 2

  def ev_keydown(self, event):
    player = self.engine.player
    key = event.sym
    index = key - tcod.event.K_a

    if 0 <= index <= 26:
      # Did they push a letter between a and z
      try:
        selected_item = player.inventory.items[index]
      except IndexError:
        self.engine.message_log.add_message('Invalid entry.', color.invalid)
        return None
      return self.on_item_selected(selected_item)
    return super().ev_keydown(event)

  def on_item_selected(self, item):
    """Called when the user selectes a valid item."""
    raise NotImplementedError()

class InventoryActivateHandler(InventoryEventHandler):
  """Handle using an inventory item."""

  TITLE = 'Select an item to use'

  def on_item_selected(self, item):
    """Return the action for the selected item"""
    if item.consumable:
      return item.consumable.get_action(self.engine.player)
    elif item.equippable:
      return actions.EquipAction(self.engine.player, item)
    else:
      return None

class InventoryEnergizeHandler(InventoryEventHandler):
  """Handle energizing an inventory item."""

  TITLE = 'Select an item to energize'
  def __init__(self, engine, energizer):
    super().__init__(engine)
    self.energizer = energizer

  def on_item_selected(self, item):
    """Return the action for the selected item"""
    return actions.EnergizeAction(self.engine.player, self.energizer, item)

class InventoryDropHandler(InventoryEventHandler):
  """Handle dropping an inventory item"""

  TITLE = 'Select and item to drop'

  def on_item_selected(self, item):
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

    if key == tcod.event.K_PERIOD and modifier & (
      tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
    ):
      return actions.TakeStairsAction(player)

    if key in MOVE_KEYS:
      dx, dy = MOVE_KEYS[key]
      action = BumpAction(player, dx, dy)
    elif key in WAIT_KEYS:
      action = WaitAction(player)

    elif key in (tcod.event.K_ESCAPE, tcod.event.K_q):
      raise SystemExit()
    elif key == tcod.event.K_v:
      return HistoryViewer(self.engine)
    elif key == tcod.event.K_g:
      action = PickupAction(player)

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
      return LookHandler(self.engine)

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
    self.on_quit()

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

    log_console = tcod.Console(console.width - 6, console.height - 6)

    # Draw a frame with a custom banner title.
    log_console.draw_frame(0, 0, log_console.width, log_console.height)
    log_console.print_box(
        0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
    )

    # Render the message log using the cursor parameter.
    self.engine.message_log.render_messages(
        log_console,
        1,
        1,
        log_console.width - 2,
        log_console.height - 2,
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
