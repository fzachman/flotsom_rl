import tcod
from input_handlers import BaseEventHandler
import color
import tile_types
import numpy as np

class CreatorEventHandler(BaseEventHandler):
  def __init__(self, engine):
    self.engine = engine

class CreatorMainMenu(CreatorEventHandler):
  """ Handle the main menu rendering and input """

  def on_render(self, console):
    menu_width = 24
    for i, text in enumerate(
      ['[B] Brush Editor', '[S] Brush Set Editor', '[Q] Quit']
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
    elif event.sym == tcod.event.K_b:
      return BrushMainMenu(self.engine)

    return None


class BrushMainMenu(CreatorEventHandler):
  def on_render(self, console):
    menu_width = 24
    for i, text in enumerate(
      ['[N] New Brush', '[E] Edit Brush', '[Esc] Back']
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
      return CreatorMainMenu(self.engine)
    elif event.sym == tcod.event.K_n:
      return TextInputHandler(self, self.new_brush, ['Enter brush name','Select a brush size'])
    elif event.sym == tcod.event.K_e:
      return BrushSelectHandler(self.engine,
                                callback=self.edit_brush,
                                brushes=self.engine.list_brushes())

    return None

  def edit_brush(self, brush):
    if brush:
      return DrawBrushHandler(self.engine, brush)
    else:
      return self

  def new_brush(self, responses):
    brush_name = responses[0].strip()
    brush_size = responses[1].strip()
    brush = self.engine.new_brush(brush_name, brush_size)
    return DrawBrushHandler(self.engine, brush)


class TextInputHandler(CreatorEventHandler):
  """ Display a popup text window."""
  def __init__(self, parent, callback, prompts):
    super().__init__(parent.engine)
    self.parent = parent
    self.callback = callback
    if type(prompts) == str:
      prompts = [prompts]
    self.prompts = prompts
    self.responses = []
    self.current_prompt = 0
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
      self.prompts[self.current_prompt],
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

  def ev_keyup(self, event):
    key = event.sym

    if key == tcod.event.K_BACKSPACE:
      self.text = self.text[0:-1]
    elif key == tcod.event.K_ESCAPE:
      return self.parent
    elif key == tcod.event.K_RETURN:
      self.responses.append(self.text)
      if len(self.responses) < len(self.prompts):
        self.current_prompt += 1
        self.text = ''
      else:
        responses = self.responses
        if len(responses) == 1:
          responses = responses[0]
        return self.callback(self.responses)

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


class BrushSelectHandler(CreatorEventHandler):
  def __init__(self, engine, callback, brushes, selected=set(),allow_multiple=False):
    super().__init__(engine)
    self.callback = callback
    self.brushes = brushes
    self.max_brush_size = 1
    for b in self.brushes:
      self.max_brush_size = b.size > self.max_brush_size and b.size or self.max_brush_size

    self.allow_multiple=allow_multiple
    self.brush_render_size = self.max_brush_size + 4
    self.brushes_per_row = 70 // self.brush_render_size
    self.max_rows = 40 // self.brush_render_size
    self.brushes_per_page = self.brushes_per_row * self.max_rows
    self.last_page = len(self.brushes) // self.brushes_per_page
    if self.last_page * self.brushes_per_page < len(self.brushes):
      self.last_page += 1 # Incomplete page

    self.selected_brushes = selected
    self.current_position = (0,0)
    self.page = 0

  def ev_keyup(self, event):
    sym = event.sym

    current_x, current_y = self.current_position
    visible_brushes = self.get_visible_brushes

    if sym == tcod.event.K_ESCAPE:
      return BrushMainMenu(self.engine)
    elif sym == tcod.event.K_SPACE:
      self.select_brush()
      if not self.allow_multiple and len(self.selected_brushes) > 0:
        return self.callback(self.selected_brushes.pop())

    elif sym == tcod.event.K_RETURN:
      if not self.allow_multiple:
        self.select_brush()
        return self.callback(self.selected_brushes.pop())

      return self.callback(self.selected_brushes)

    elif sym == tcod.event.K_UP:
      if current_y > 0:
        current_y = 1
      elif self.page > 0:
          self.page -= 1
          current_y = self.max_rows - 1

    elif sym == tcod.event.K_DOWN:
      if current_y < self.max_rows - 1:
        current_y += 1
      elif self.page < self.last_page:
        self.page += 1
        current_y = 0

    elif sym == tcod.event.K_LEFT:
      if current_x > 0:
        current_x -= 1

    elif sym == tcod.event.K_RIGHT:
      if current_x <= self.brushes_per_row - 1:
        current_x += 1

    elif sym == tcod.event.K_PAGEUP:
      if self.page > 0:
        self.page -= 1
    elif sym == tcod.event.K_PAGEDOWN:
      if self.page < self.last_page:
        self.page += 1

    self.current_position = (current_x, current_y)

  def select_brush(self):
    index = self.brushes_per_page * self.page
    index += (self.current_position[1]) * self.brushes_per_row
    index += self.current_position[0]
    if index < len(self.brushes):
      print(index, self.brushes)
      selected_brush = self.brushes[index]
      if selected_brush in self.selected_brushes:
        self.selected_brushes.remove(selected_brush)
      else:
        self.selected_brushes.add(selected_brush)

  def get_visible_brushes(self):
    return self.brushes[self.brushes_per_page * self.page: self.brushes_per_page * (self.page +1)]

  def on_render(self, console):
    console.clear(fg=(255,255,255),bg=(20,20,60))
    title = 'Select brush'
    if self.allow_multiple:
      title += 'es'
    # Frame around the whole brush menu
    console.draw_frame(0,0,console.width,console.height,title)
    # Render each brush with enough space to allow
    # a highlight and a blank separator

    visible_brushes = self.get_visible_brushes()
    # Pad our list with empty values so we can reshape it to fill the screen
    visible_brushes.extend([None] * (self.brushes_per_row - (len(visible_brushes) % self.brushes_per_row)))
    #print(len(visible_brushes), self.brushes_per_row, len(visible_brushes) // self.brushes_per_row)
    visible_brushes = np.array(visible_brushes).reshape(len(visible_brushes) // self.brushes_per_row, self.brushes_per_row)

    for y in range(len(visible_brushes)):
      for x in range(len(visible_brushes[0])):
        brush = visible_brushes[y,x]
        if brush:
          r_x = x * self.brush_render_size
          r_y = y * self.brush_render_size
          if brush in self.selected_brushes:
            select_display = np.full((brush.size+2,brush.size+2),fill_value=128, dtype='i,i,i')
            console.tiles_rgb[r_x+1:r_x+3+brush.size,r_y+1:r_y+3+brush.size]=select_display
          brush.render(console,r_x+2,r_y+2)
          #print(x, y, self.current_position)
          if (x,y) == self.current_position:
            #print('Higlighting selected')
            fg = (0,0,255)
            console.draw_frame(x=r_x+1,y=r_y+1, width=brush.size+2,height=brush.size+2,fg=fg)


class DrawBrushHandler(CreatorEventHandler):
  def __init__(self, engine, brush):
    super().__init__(engine)
    self.brush = brush
    self.paint_options = (('Wall',0),('Floor',255))
    self.commands = (('R', 'Rename'),
                     ('D', 'Delete'),
                     ('S', 'Save'),
                     ('B', 'Back (save)'),
                     ('Q', 'Quit (no save)'))
    self.paint_with = 0

  def erase(self, x, y):
    self.brush.data[x,y] = 0

  def rename_brush(self, brush_name):
    brush_name = brush_name.strip()
    if brush_name:
      if brush_name in self.engine.brushes:
        self.engine.message_log.add_message('That brush name is already in use.')
      else:
        self.brush.name = text.strip()
    return self

  def delete_brush(self, confirm):
    if confirm:
      self.engine.delete_brush(self.brush)
      return self.BrushSelectHandler(self.engine)
    else:
      return self

  def ev_mousebuttondown(self, event):
    x = event.tile.x - 1
    y = event.tile.y - 1
    if event.state & tcod.event.BUTTON_LMASK == tcod.event.BUTTON_LMASK:
      if 0 <= x <= self.brush.size and \
         0 <= y <= self.brush.size:
        # We are painting on our brush
        self.brush.data[x,y] = self.paint_with
    elif event.state & tcod.event.BUTTON_RMASK == tcod.event.BUTTON_RMASK:
      self.erase(x,y)

  def ev_mousemotion(self, event):
    x = event.tile.x - 1
    y = event.tile.y - 1
    if event.state & tcod.event.BUTTON_LMASK == tcod.event.BUTTON_LMASK:
      if 0 <= x <= self.brush.size-1 and \
         0 <= y <= self.brush.size-1:
        # We are painting on our tile
        self.brush.data[x,y] = self.paint_with
    elif event.state & tcod.event.BUTTON_RMASK == tcod.event.BUTTON_RMASK:
      self.erase(x,y)

  def ev_keyup(self, event):
    key = event.sym

    if key == tcod.event.K_1:
      self.paint_with = self.paint_options[0][1]
    elif key == tcod.event.K_2:
      self.paint_with = self.paint_options[1][1]

    elif key == tcod.event.K_s:
      self.engine.save_brushes()

    elif key == tcod.event.K_d:
      return ConfirmHandler(self.engine, self, 'Are you sure you want to delete this brush?', self.delete_brush)

    elif key == tcod.event.K_b:
      self.engine.save_brushes()
      return BrushMainMenu(self.engine)

    elif key == tcod.event.K_r:
      return TextInputHandler(self, self.rename_brush, 'Select a new name')

    elif key == tcod.event.K_q:
      raise SystemExit()


  def on_render(self, console):
    self.engine.render(console)

    brush = self.brush
    console.draw_frame(0,0,brush.size+2,brush.size+2)
    brush.render(console, 1,1)

    commands_x = brush.size + 4
    commands_width = console.width - (commands_x)
    commands_height = console.height - 7
    console.draw_frame(
     x=commands_x - 1,
     y=0,
     width=commands_width,
     height = commands_height,
     title=brush.name,
     fg=(255,255,255),
     bg=(0,0,0),
     clear=True
    )

    for i, paint_option in enumerate(self.paint_options, start=1):
      console.tiles_rgb['bg'][commands_x, i] = (paint_option[1],paint_option[1],paint_option[1])
      command_title = f'({i}) {paint_option[0]}'
      if self.paint_with == paint_option[1]:
        command_title += ' (selected)'
      console.print(x=commands_x + 3, y = i, string=command_title)

    y_offset = len(self.paint_options)+3
    for i, command in enumerate(self.commands):
      command_string = '(%s) %s' % (command[0],command[1])
      console.print(x=commands_x + 3, y = y_offset + i, string=command_string)
