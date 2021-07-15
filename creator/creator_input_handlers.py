import tcod
from input_handlers import BaseEventHandler
import color
import tile_types

class CreatorEventHandler(BaseEventHandler):
  def __init__(self, engine):
    self.engine = engine

class CreatorMainMenu(CreatorEventHandler):
  """ Handle the main menu rendering and input """

  def on_render(self, console):
    menu_width = 24
    for i, text in enumerate(
      ['[N] Create new sector', '[E] Edit existing sector', '[Q] Quit']
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

  def ev_keyup(self, event):
    if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
      raise SystemExit()
    elif event.sym == tcod.event.K_n:
      return TextInputHandler(self.engine, self,'What should we call this new sector?')
    elif event.sym == tcod.event.K_e:
      return SelectSectorHandler(self.engine, self)

    return None

  def on_text_entered(self, text):
    if text.strip() == '':
      return self
    else:
      self.engine.new_sector(text)
      return DrawTileHandler(self.engine)

  def on_sector_selected(self, sector):
    print(f'Setting current sector to {sector.name}')
    self.engine.current_sector = sector
    return DrawTileHandler(self.engine)

class TextInputHandler(CreatorEventHandler):
  """ Display a popup text window."""
  def __init__(self, engine, parent_handler, prompt):
    super().__init__(engine)
    self.parent = parent_handler
    self.prompt = prompt
    self.text = ''

  def on_render(self, console):
    """ Render parent and dim result, then print message on top"""
    self.parent.on_render(console)
    console.tiles_rgb['fg'] //= 8
    console.tiles_rgb['bg'] //= 8
    x = console.width // 2
    y = console.height // 2

    console.print(
      x,
      y,
      self.prompt,
      fg=color.white,
      bg=color.black,
      alignment=tcod.CENTER,
    )
    console.print(
     x,
     y+1,
     '> ' + self.text,
     fg=color.white,
     bg=color.black,
     alignment=tcod.LEFT,
    )

  def ev_textinput(self, event):
    input_char = event.text
    self.text += input_char

  def ev_keydown(self, event):
    key = event.sym

    if key == tcod.event.K_BACKSPACE:
      self.text = self.text[0:-1]
    elif key == tcod.event.K_ESCAPE:
      return self.parent
    elif key == tcod.event.K_RETURN:
      return self.parent.on_text_entered(self.text)

class ConfirmHandler(CreatorEventHandler):
  """ Display a popup text window."""
  def __init__(self, engine, parent_handler, prompt, callback):
    super().__init__(engine)
    self.parent = parent_handler
    self.prompt = prompt
    self.callback = callback

  def on_render(self, console):
    """ Render parent and dim result, then print message on top"""
    self.parent.on_render(console)
    console.tiles_rgb['fg'] //= 8
    console.tiles_rgb['bg'] //= 8
    x = console.width // 2
    y = console.height // 2

    console.print(
      x,
      y,
      self.prompt,
      fg=color.white,
      bg=color.black,
      alignment=tcod.CENTER,
    )
    console.print(
     x,
     y+1,
     '(Y/N)',
     fg=color.white,
     bg=color.black,
     alignment=tcod.CENTER,
    )

  def ev_keydown(self, event):
    key = event.sym
    if key == tcod.event.K_y:
      return self.callback(True)
    else:
      return self.callback(False)


class SectorViewHandler(CreatorEventHandler):
  def render_sector(self, console, sector=None):
    # Highlight the sector area
    console.draw_frame(
      x=0,
      y=0,
      width = sector.width+2,
      height = sector.height+2,
      fg=(255,255,255),
      clear=False,
    )
    if sector:
      # Draw the sectors name
      title = sector.name[0:sector.width]
      title_x = (sector.width + 2) // 2
      if title_x < 1:
        title_x = 1

      console.print(x=title_x, y=0, string=title, fg=(255,255,255), alignment=tcod.CENTER)

      # Render the current sector if selected
      console.tiles_rgb[1:sector.width+1, 1:sector.height+1] = sector.tiles['light']


class SelectSectorHandler(SectorViewHandler):
  def __init__(self, engine, parent):
    super().__init__(engine)
    self.parent = parent
    self.current_sector = None
    self.current_index = None
    self.all_sectors = list(enumerate(self.engine.sectors, start=1))
    if len(self.all_sectors) > 0:
      self.current_sector = self.all_sectors[0][1]
      self.current_index = 0

  def ev_keyup(self, event):
    sym = event.sym

    if sym == tcod.event.K_ESCAPE:
      return CreatorMainMenu(self.engine)
    elif self.current_index is not None:
      if sym == tcod.event.K_RETURN:
        return self.parent.on_sector_selected(self.current_sector)
      if sym == tcod.event.K_DOWN:
        if self.current_index < len(self.all_sectors) - 1:
          self.current_index += 1
      elif sym == tcod.event.K_UP:
        if self.current_index > 0:
          self.current_index -= 1

      self.current_sector = self.all_sectors[self.current_index][1]

  def on_render(self, console):
    sector = self.current_sector
    self.render_sector(console, sector)

    menu_x = sector.width + 3
    menu_width = console.width - (sector.width +3)
    menu_height = console.height - 1 # Leave some room for feedback later
    console.draw_frame(
     x=menu_x,
     y=0,
     width=menu_width,
     height = menu_height,
     fg=(255,255,255),
     clear=True
    )

    console.print(x=(menu_x + menu_width) // 2, y=0, string='Select a Sector', fg=(255,255,255), alignment=tcod.CENTER)
    if len(self.all_sectors) == 0:
      console.print(x=menu_x + 2, y = 1, string="No sectors defined!", alignment=tcod.LEFT)
    else:
      for i, sector in self.all_sectors:
        sector_name = sector.name
        menu_option = f'{i}) {sector_name}'
        bg = (0,0,0)
        fg = (255,255,255)
        if self.current_sector == sector:
          fg = (0,0,0)
          bg = (255,255,255)
        console.print(x=menu_x + 2, y = i, string=sector_name,bg=bg,fg=fg,alignment=tcod.LEFT)



class DrawTileHandler(SectorViewHandler):
  def __init__(self, engine):
    super().__init__(engine)
    self.paint_with = tile_types.floor_room
    self.current_sector = self.engine.current_sector

  def erase(self, x, y):
    self.current_sector.tiles[x,y] = tile_types.wall

  def on_text_entered(self, text):
    if text:
      self.current_sector.name = text
    return self

  def ev_mousebuttondown(self, event):
    x = event.tile.x - 1
    y = event.tile.y - 1
    if event.state & tcod.event.BUTTON_LMASK == tcod.event.BUTTON_LMASK:
      if 0 <= x <= self.current_sector.width and \
         0 <= y <= self.current_sector.height:
        # We are painting on our tile
        self.current_sector.tiles[x,y] = self.paint_with
    elif event.state & tcod.event.BUTTON_RMASK == tcod.event.BUTTON_RMASK:
      self.erase(x,y)

  def ev_mousemotion(self, event):
    x = event.tile.x - 1
    y = event.tile.y - 1
    if event.state & tcod.event.BUTTON_LMASK == tcod.event.BUTTON_LMASK:
      if 0 <= x <= self.current_sector.width and \
         0 <= y <= self.current_sector.height:
        # We are painting on our tile
        self.current_sector.tiles[x,y] = self.paint_with
    elif event.state & tcod.event.BUTTON_RMASK == tcod.event.BUTTON_RMASK:
      self.erase(x,y)

  def ev_keydown(self, event):
    key = event.sym

    if key == tcod.event.K_1:
      self.paint_with = tile_types.floor_room
    elif key == tcod.event.K_2:
      self.paint_with = tile_types.floor_hall
    elif key == tcod.event.K_3:
      self.paint_with = tile_types.floor_transition
    elif key == tcod.event.K_4:
      self.paint_with = tile_types.wall
    elif key == tcod.event.K_5:
      self.paint_with = tile_types.exit_point

    elif key == tcod.event.K_s:
      self.engine.save_sectors()

    elif key == tcod.event.K_d:
      return ConfirmHandler(self.engine, self, 'Are you sure you want to delete this sector?', self.delete_sector)

    elif key == tcod.event.K_b:
      self.engine.save_sectors()
      return CreatorMainMenu(self.engine)

    elif key == tcod.event.K_r:
      return TextInputHandler(self.engine, self, 'Select a new name')

    elif key == tcod.event.K_q:
      raise SystemExit()

  def delete_sector(self, confirm):
    if confirm:
      self.engine.delete_sector()

    return CreatorMainMenu(self.engine)

  def on_render(self, console):
    sector = self.current_sector
    self.render_sector(console, sector)

    commands_x = sector.width + 3
    commands_width = console.width - (sector.width +3)
    commands_height = console.height - 1 # Leave some room for feedback later
    console.draw_frame(
     x=commands_x,
     y=0,
     width=commands_width,
     height = commands_height,
     fg=(255,255,255),
     clear=True
    )

    console.print(x=(commands_x + commands_width) // 2, y=0, string='Commands', fg=(255,255,255), alignment=tcod.CENTER)
    tile_types_list = (('Room', tile_types.floor_room),
                  ('Hall', tile_types.floor_hall),
                  ('Transition', tile_types.floor_transition),
                  ('Wall', tile_types.wall),
                  ('Exit', tile_types.floor_airlock))
    for i, data in enumerate(tile_types_list,start=1):
      tile_name = data[0]
      tile_type = data[1]
      console.tiles_rgb['bg'][commands_x + 1,i] = tile_type['light']['bg']
      console.tiles_rgb['fg'][commands_x + 1,i] = tile_type['light']['fg']
      command_title = f'{i}) {tile_name}'
      if tile_type == self.paint_with:
        command_title += (' (selected)')
      console.print(x=commands_x + 3, y = i, string=command_title)


    console.print(x=commands_x + 1, y = len(tile_types_list)+4, string='R) Rename')
    console.print(x=commands_x + 1, y = len(tile_types_list)+5, string='D) Delete')
    console.print(x=commands_x + 1, y = len(tile_types_list)+6, string='S) Save')
    console.print(x=commands_x + 1, y = len(tile_types_list)+7, string='B) Back')
    console.print(x=commands_x + 1, y = len(tile_types_list)+8, string='Q) Quit')
