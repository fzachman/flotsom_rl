#!/usr/bin/env python3
import traceback

import tcod

import color
import exceptions
import input_handlers
import setup_game

def save_game(handler, filename):
  """If the current event handler has an active Engine, then save it."""
  if isinstance(handler, input_handlers.EventHandler):
    handler.engine.save_as(filename)
    print('Game saved.')


def flush_animations(context, console, engine):
  if len(engine.animation_queue) > 0:
    for animation in engine.dequeue_animation():
      for frame in animation.animate(console, engine):
        context.present(frame)
    context.present(console)

def main():
  screen_width = 80
  screen_height = 50

  #tileset = tcod.tileset.load_tilesheet('dejavu10x10_gs_tc.png', 32, 8, tcod.tileset.CHARMAP_TCOD)
  #tileset = tcod.tileset.load_tilesheet('16x16_sb_ascii.png', 16, 16, tcod.tileset.CHARMAP_CP437)
  cmap = tcod.tileset.CHARMAP_CP437.copy()
  cmap.extend([9624, 9629,9622, 9626, 9623, 0,0,0,0,0,0,0,0,0,0,0])
  tileset = tcod.tileset.load_tilesheet('16x16_sb_ascii_flotsom.png', 16, 17, cmap)
  handler = setup_game.MainMenu()

  with tcod.context.new_terminal(
    screen_width,
    screen_height,
    tileset=tileset,
    title='FlotsomRL',
    vsync=True,
  ) as context:
    root_console = tcod.Console(screen_width, screen_height, order="F")

    should_render = True
    try:
      while True:
        # We need to render the results of the last handler the user activated
        if should_render:
          root_console.clear()
          handler.on_render(console=root_console)
          context.present(root_console)
          # But don't keep rendering it if we are just waking up to orbit stuff
          should_render = False

        if hasattr(handler, 'engine'):
          if handler.engine.is_enemy_turn:
            for enemy_turn in handler.engine.handle_enemy_turns():
              handler.engine.update_light_levels()
              try:
                flush_animations(context, root_console, handler.engine)
              except:
                # Ignore animation errors for now.
                pass

            handler.engine.update_vacuum()
            should_render = True

          if handler.engine.orbit():
            should_render = True

        if should_render:
          root_console.clear()
          handler.on_render(console=root_console)
          context.present(root_console)
          should_render = False

        try:
          for event in tcod.event.wait(.1):
            should_render = True
            context.convert_event(event)
            handler = handler.handle_events(event)
        except Exception:
          traceback.print_exc() # Print error to stderr
          # Then print the error to the message log
          if isinstance(handler, input_handlers.EventHandler):
            handler.engine.message_log.add_message(traceback.format_exc(), color.error)
    except exceptions.QuitWithoutSaving:
      raise
    except SystemExit: # Save and Quit
      save_game(handler, 'savegame.sav')
      raise
    except BaseException: # Save on any other unexpected exception
      save_game(handler, 'savegame.sav')
      raise



if __name__ == '__main__':
  main()
