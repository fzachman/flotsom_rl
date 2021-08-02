import copy
import lzma
import pickle
import traceback
import tcod

import color
from engine import Engine
import entity_factories
from game_map import GameWorld
import input_handlers

from creator.creator_input_handlers import CreatorMainMenu
from creator.engine import CreatorEngine


background_image = tcod.image.load('menu_background.png')[:,:,:3]


def new_game():
  """ Return a brand new game session as an Engine instance"""
  #map_width = 80#80
  #map_height = 80#43

  # The map can be bigger than the renderable area
  # This is the size of the viewport the player sees
  # of the map
  viewport_width = 80
  viewport_height = 43

  #room_max_size = 10
  #room_min_size = 6
  #max_rooms = 60

  #tileset = tcod.tileset.load_tilesheet('dejavu10x10_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD)

  player = copy.deepcopy(entity_factories.player)
  engine = Engine(player=player)

  engine.game_world = GameWorld(engine=engine,
                                viewport_width=viewport_width,
                                viewport_height=viewport_height
                                )

  engine.game_world.generate_floor()

  engine.update_fov()
  engine.update_vacuum()

  engine.message_log.add_message('Hello and welcome, adventurer, to yet another dungeon!', color.welcome_text)

  from components.effects import Knockback, ChainLightning

  knife = copy.deepcopy(entity_factories.knife)
  spacer_suit = copy.deepcopy(entity_factories.spacer_suit)
  popgun = copy.deepcopy(entity_factories.popgun)
  neural_scrambler = copy.deepcopy(entity_factories.neural_scrambler)
  power_fist = copy.deepcopy(entity_factories.power_fist)

  power_fist.equippable.add_after_melee_damage_effect(Knockback(1))
  popgun.equippable.add_after_ranged_damage_effect(ChainLightning(1))

  knife.parent = player.inventory
  spacer_suit.parent = player.inventory
  popgun.parent = player.inventory
  neural_scrambler.parent = player.inventory
  power_fist.parent = player.inventory

  player.inventory.items.append(knife)
  player.equipment.toggle_equip(knife, add_message=False)

  player.inventory.items.append(spacer_suit)
  player.equipment.toggle_equip(spacer_suit, add_message=False)

  player.inventory.items.append(popgun)
  player.inventory.items.append(neural_scrambler)
  player.inventory.items.append(power_fist)


  return engine

def load_game(filename):
  """Load an engine instance from a file."""
  with open(filename, 'rb') as f:
    engine = pickle.loads(lzma.decompress(f.read()))
  assert isinstance(engine, Engine)
  return engine

def launch_creator():
  engine = CreatorEngine()
  return engine

class MainMenu(input_handlers.BaseEventHandler):
  """ Handle the main menu rendering and input """

  def on_render(self, console):
    console.draw_semigraphics(background_image, 0, 0)

    console.print(
      console.width // 2,
      console.height // 2 - 4,
      "FlotsomRL",
      fg=color.menu_title,
      alignment=tcod.CENTER,
    )
    console.print(
      console.width // 2,
      console.height - 2,
      "By Forest Zachman",
      fg=color.menu_title,
      alignment=tcod.CENTER,
    )

    menu_width = 24
    for i, text in enumerate(
      ['[N] Play a new game', '[C] Continue last game', '[Q] Quit', '[B] Builder']
    ):
      console.print(
        console.width // 2,
        console.height // 2 - 2 + i,
        text.ljust(menu_width),
        fg=color.menu_text,
        bg=color.black,
        alignment=tcod.CENTER,
        bg_blend=tcod.BKGND_ALPHA(64),
      )

  def ev_keydown(self, event):
    if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
      raise SystemExit()
    elif event.sym == tcod.event.K_c:
      try:
        return input_handlers.MainGameEventHandler(load_game('savegame.sav'))
      except FileNotFoundError:
        return input_handlers.PopupMessage(self, 'No saved game to load.')
      except Exception as exec:
        traceback.print_exc()
        return input_handlers.PopupMessage(self, f'Failed to load save:\n{exc}')

    elif event.sym == tcod.event.K_n:
      return input_handlers.MainGameEventHandler(new_game())

    elif event.sym == tcod.event.K_b:
      return CreatorMainMenu(launch_creator())

    return None
