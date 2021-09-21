import lzma
import pickle
import time

from collections import deque

import tcod
from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
import exceptions
from message_log import MessageLog
import render_functions
import color

class Engine:

  def __init__(self, player):
    self.message_log = MessageLog()
    self.mouse_location = (0,0)
    self.player = player
    self.time_to_orbit = 1
    self.last_update = time.time()

    self.animation_queue = deque()
    self.is_enemy_turn = False

  def queue_animation(self, animation):
    self.animation_queue.append(animation)

  def dequeue_animation(self):
    while len(self.animation_queue) > 0:
      yield self.animation_queue.popleft()

  def handle_enemy_turns(self):
    #if not self.is_enemy_turn:
    #  return
    for entity in set(self.game_map.actors) - {self.player}:
      if entity.ai:
        try:
          entity.ai.perform()
        except exceptions.Impossible:
          pass # Ignore impossible actions from AI
        yield 1

    self.is_enemy_turn = False


  def update_fov(self):
    """ Recompute visible area for player POV """
    self.game_map.visible[:] = compute_fov(
      self.game_map.tiles['transparent'],
      (self.player.x, self.player.y),
      radius=self.player.visibility,
      algorithm=tcod.FOV_BASIC
    )
    #self.game_map.dim[:] = compute_fov(
    #  self.game_map.tiles['transparent'],
    #  (self.player.x, self.player.y),
    #  radius=8,
    #  algorithm=tcod.FOV_BASIC
    #)

    # If a tile is visible, it should be added to explored
    #self.game_map.explored |= self.game_map.visible
    #self.game_map.explored |= self.game_map.dim

  def update_light_levels(self):
    """ Create our light map for all static light entities """
    self.game_map.light_levels[:] = 1
    for light in [self.player]:#self.game_map.lights:
      if light == self.player:
        light_walls = True
      else:
        light_walls = self.game_map.visible[light.x][light.y]
      coords = self.game_map.get_coords_in_radius(light.x, light.y, light.light_source.radius)
      light_fov = compute_fov(
        self.game_map.tiles['transparent'],
        (light.x, light.y),
        radius=light.light_source.radius,
        algorithm=tcod.FOV_BASIC,
        light_walls=light_walls
      )
      for x, y in coords:
        if light_fov[x][y]:
          distance = light.distance(x, y)
          brightness_diff = distance / (light.light_source.radius+2)
          if brightness_diff < self.game_map.light_levels[x][y]:
            self.game_map.light_levels[x][y] = brightness_diff

    explored = (self.game_map.light_levels < 1) & self.game_map.visible
    self.game_map.explored |= explored

  def update_vacuum(self):
    """ Mark tiles affected by vacuum sources """
    vacuumed     = set()
    for source in self.game_map.vacuum_sources:
      vacuumed.update(self._vacuum(source, vacuumed))

    vacuum_tiles = set()
    for room in vacuumed:
      vacuum_tiles.update(room.coords)
      vacuum_tiles.update(room.exits)
      #for x,y in room.coords.union(room.exits):
      #  self.game_map.vacuum[x,y] = True
    self.game_map.vacuum_tiles = vacuum_tiles

  def breath(self):
    for actor in self.game_map.actors:
      if (actor.x,actor.y) in self.game_map.vacuum_tiles:
        actor.lungs.breath()

  def orbit(self):
    did_orbit = False
    if time.time() - self.last_update >= 1:
      space_tiles = self.game_map.space_tiles
      wrap = space_tiles[0:1, 0:len(space_tiles[0])]
      space_tiles[0:len(space_tiles)-1, 0:len(space_tiles[0])] = space_tiles[1:len(space_tiles), 0:len(space_tiles[1])]
      space_tiles[len(space_tiles)-1:len(space_tiles), 0:len(space_tiles[0])] = wrap

      tiles = self.game_map.tiles
      for x in range(len(tiles)-1, 0, -1):
        for y in range(0, len(tiles[0])-1):
          if tiles[x][y]['tile_class'] == 'space':
            tiles[x][y] = space_tiles[x][y]
      did_orbit = True
      self.last_update = time.time()
    return did_orbit

  def _vacuum(self, room, vacuumed):
    """shlorp shlorp!"""
    vacuumed.add(room)
    #print(f'Vacuuming room with {len(room.connecting_rooms)} neighbors')
    for neighbor in room.connecting_rooms:
      if neighbor not in vacuumed:
        connecting_exits = neighbor.exits.intersection(room.exits)
        #print(f'Checking my exits {room.exits} against neighbor exits {neighbor.exits} and found {connecting_exits}')
        for exit in connecting_exits:
          if self.game_map.tiles[exit[0],exit[1]]['walkable']:
            #print(f'Found neighbor to vacuum at exit ({exit[0]},{exit[1]}).  Spreading!')
            # Might need a "permeable" attribute at some point if we want
            # tiles to allow air out without being walkable
            vacuumed.update(self._vacuum(neighbor, vacuumed))
            break
          else:
            #print(f'Neighbor exit at ({exit[0]},{exit[1]}) is sealed.  You are safe for now!')
            pass
    return vacuumed

  def render(self, console):
    self.game_map.render(console)

    info_pane_x = self.game_world.viewport_width
    info_pane_width = console.width - info_pane_x
    info_pane_height = self.game_world.viewport_height
    # This is debug info.  Remove it later
    info_pane_title = f'({self.player.x},{self.player.y})'
    render_functions.draw_window(console, info_pane_x, 0, info_pane_width, info_pane_height, info_pane_title)

    sub_pane_x = info_pane_x + 1
    sub_pane_width = info_pane_width - 2

    bar_pane_x = sub_pane_x
    bar_pane_y = 1
    bar_pane_width = sub_pane_width
    bar_pane_height = 5
    render_functions.draw_window(console, bar_pane_x, bar_pane_y, bar_pane_width, bar_pane_height, '')

    render_functions.render_bar(console=console,
                                x=bar_pane_x + 1,
                                y=bar_pane_y + 1,
                                current_value=self.player.fighter.hp,
                                maximum_value=self.player.fighter.max_hp,
                                total_width=bar_pane_width -2,
                                text='HP',
                                bar_number=0)

    render_functions.render_bar(console=console,
                                x=bar_pane_x + 1,
                                y=bar_pane_y + 2,
                                current_value=self.player.lungs.current_o2,
                                maximum_value=self.player.lungs.max_o2,
                                total_width=bar_pane_width -2,
                                text='Oxygen',
                                text_color=color.o2_bar_text,
                                full_color=color.o2_bar_filled,
                                empty_color=color.o2_bar_empty)

    if self.player.fighter.max_shields > 0:
      render_functions.render_bar(console=console,
                                  x=bar_pane_x + 1,
                                  y=bar_pane_y + 3,
                                  current_value=self.player.fighter.shields,
                                  maximum_value=self.player.fighter.max_shields,
                                  total_width=bar_pane_width -2,
                                  text='Shields',
                                  text_color=color.shield_bar_text,
                                  full_color=color.shield_bar_filled,
                                  empty_color=color.shield_bar_empty)


    char_pane_x =  sub_pane_x
    char_pane_y = bar_pane_y + bar_pane_height
    char_pane_width = sub_pane_width
    char_pane_height = 9
    render_functions.draw_window(console, char_pane_x, char_pane_y, char_pane_width, char_pane_height, '')

    console.print(
      x=char_pane_x + 1, y=char_pane_y + 1, string=f"Level: {self.player.level.current_level}"
    )
    console.print(
      x=char_pane_x + 1, y=char_pane_y + 2, string=f"XP: {self.player.level.current_xp}"
    )
    console.print(
      x=char_pane_x + 1,
      y=char_pane_y + 3,
      string=f"XP for next Level: {self.player.level.experience_to_next_level}",
    )
    fighter = self.player.fighter
    console.print(
      x=char_pane_x + 1, y=char_pane_y + 4, string=f"Melee: {fighter.power} ({fighter.base_power}+{fighter.power_bonus})"
    )
    console.print(
      x=char_pane_x + 1, y=char_pane_y + 5, string=f"Ranged: {fighter.accuracy} ({fighter.base_accuracy}+{fighter.accuracy_bonus})"
    )
    console.print(
      x=char_pane_x + 1, y=char_pane_y + 6, string=f"Defense: {fighter.defense} ({fighter.base_defense}+{fighter.defense_bonus})"
    )
    render_functions.render_dungeon_level(console=console,
                                          dungeon_level=self.game_world.current_floor,
                                          location=(char_pane_x + 1,char_pane_y + 7))

    equip_pane_x = sub_pane_x
    equip_pane_y = char_pane_y + char_pane_height
    equip_pane_width = sub_pane_width
    equip_pane_height = (len(self.player.equipment.item_slots) * 2) + 2
    render_functions.draw_window(console, equip_pane_x, equip_pane_y, equip_pane_width, equip_pane_height, 'Equipped')

    equip_y = equip_pane_y + 1
    equip_x = equip_pane_x + 1
    for slot in self.player.equipment.item_slots:
      console.print(equip_x, equip_y, slot.slot_name)
      if slot.item:
        item_name = f'-{slot.item.name}'
        if slot.item.powered:
          item_name = f'{item_name} ({slot.item.powered.current_power}/{slot.item.powered.max_power})'
      else:
        item_name = '-(Empty)'
      console.print(equip_x, equip_y + 1, item_name)
      equip_y += 2


    log_pane_x = sub_pane_x
    log_pane_y = equip_pane_y + equip_pane_height
    log_pane_width = sub_pane_width
    log_pane_height = info_pane_height - log_pane_y - 1
    render_functions.draw_window(console, log_pane_x, log_pane_y, log_pane_width, log_pane_height, '')

    self.message_log.render(console=console,x=log_pane_x+1,y=log_pane_y+1,width=log_pane_width-2,height=log_pane_height-2)

    render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=self)

  def save_as(self, filename):
    """ Save this Engine instance as a compressed file."""
    save_data = lzma.compress(pickle.dumps(self))
    with open(filename, 'wb') as f:
      f.write(save_data)
