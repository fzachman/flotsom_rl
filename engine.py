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
