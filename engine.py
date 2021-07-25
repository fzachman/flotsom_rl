import lzma
import pickle

import tcod
from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
import exceptions
from message_log import MessageLog
import render_functions

class Engine:

  def __init__(self, player):
    self.message_log = MessageLog()
    self.mouse_location = (0,0)
    self.player = player

  def handle_enemy_turns(self):
    for entity in set(self.game_map.actors) - {self.player}:
      if entity.ai:
        try:
          entity.ai.perform()
        except exceptions.Impossible:
          pass # Ignore impossible actions from AI

  def update_fov(self):
    """ Recompute visible area for player POV """
    self.game_map.visible[:] = compute_fov(
      self.game_map.tiles['transparent'],
      (self.player.x, self.player.y),
      radius=5,
      algorithm=tcod.FOV_BASIC
    )
    self.game_map.dim[:] = compute_fov(
      self.game_map.tiles['transparent'],
      (self.player.x, self.player.y),
      radius=8,
      algorithm=tcod.FOV_BASIC
    )

    # If a tile is visible, it should be added to explored
    self.game_map.explored |= self.game_map.visible
    self.game_map.explored |= self.game_map.dim

  def render(self, console):
    self.game_map.render(console)

    self.message_log.render(console=console,x=21,y=45,width=40,height=5)

    render_functions.render_bar(console=console,
                                current_value=self.player.fighter.hp,
                                maximum_value=self.player.fighter.max_hp,
                                total_width=20)

    render_functions.render_dungeon_level(console=console,
                                          dungeon_level=self.game_world.current_floor,
                                          location=(0,47))

    console.print(x=0,y=48,string=f'({self.player.x},{self.player.y})')

    render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=self)

  def save_as(self, filename):
    """ Save this Engine instance as a compressed file."""
    save_data = lzma.compress(pickle.dumps(self))
    with open(filename, 'wb') as f:
      f.write(save_data)
