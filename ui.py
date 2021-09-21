import render_functions
import color
import tcod

class BasicMenu:
  """ A basic menu class that takes a list of strings and renders with a visibly selected
  option.  Handlers that want to allow you to choose a menu option should create an instance
  of this class to handle the rendering and selection."""
  def __init__(self, options, x, y, height, width, title='', cursor=0):
    self.options = options # List of string options
    self.cursor = cursor # The currently selected option, default to 0 (first option)
    # Basic window position for rendering
    self.x = x
    self.y = y
    self.height = height
    self.width = width
    self.title = title

    # This handles scrolling for menus with more options than can be
    # displayed at once.
    self.num_visible = self.height - 2
    self.visible_slice = slice(0, self.num_visible)

  def up(self):
    if self.cursor > 0:
      self.select(self.cursor - 1)

  def down(self):
    if self.cursor < len(self.options) - 1:
      self.select(self.cursor + 1)

  def mouse_select(self, x, y):
    """ This function handles both mouse movement, which highlights whichever
    option you're hovering over, and also mouse clicking, which will return
    the selected option if you've actually clicked on one."""
    if self.x < x < self.x + self.width - 1 and \
       self.y < y < self.y + self.height - 1:
      # Ok, we're in bounds of the menu.  Check that we're over a list option
      if y < self.y + self.num_visible + 1:
        # Translate our y coord into an index of our options list, offset by any
        # scrolling that's been done
        selected = y - self.y + self.visible_slice.start - 1
        #print(f'{y}, {selected}')
        self.select(selected)
        return selected
    return None

  def select(self, index):
    """ The primary purpose of this function is to update self.visible_slice when
    we select an index that's outside the bounds of what's being displayed. ie. scrolling """
    #print(f'Cursor: {index}')
    self.cursor = index
    # Check to see if we've scrolled outside our visible list of options and update our visible slice
    if self.cursor < self.visible_slice.start:
      #print(f'Scrolling up. Cursor: {index}.  Current Slice: {self.visible_slice.start}:{self.visible_slice.stop}')
      self.visible_slice = slice(index, index + self.num_visible)
    elif self.cursor >= self.visible_slice.stop:
      start = index - self.num_visible + 1
      if start <= 0:
        start = 0
      #print(f'Scrolling down. Cursor: {index}.  Current Slice: {self.visible_slice.start}:{self.visible_slice.stop}')
      self.visible_slice = slice(start, start + + self.num_visible)

    #print(f'New Slice: {self.visible_slice.start}:{self.visible_slice.stop}')

  def render(self, console):
    # Draw the outer window
    render_functions.draw_window(console, self.x, self.y, self.width, self.height, self.title)
    # Get the options visible after scrolling
    visible_options = self.options[self.visible_slice]
    # If we've scrolled, this represents the difference between the index of our visible
    # list vs. the actual index to self.options
    cursor_offset = self.visible_slice.start

    opt_width = self.width - 2
    opt_x = self.x + 1
    for i, opt in enumerate(visible_options):
      opt = opt[0:opt_width]
      if i == self.cursor - cursor_offset:
        bg = color.menu_selected_background
      else:
        bg = color.menu_background

      # Later we may want to allow for centered or right justified menus
      # so just use the print_box function.
      console.print_box(x=opt_x,
                        y=self.y + i + 1,
                        width=opt_width,
                        height=1,
                        fg=color.menu_text,
                        bg=bg,
                        string=opt,
                        alignment=tcod.LEFT)

class InfoPane:
  """ Displays info about an entity. """
  def __init__(self, x, y, entity):
    """x,y is the origin point of the info pane.  The pane will
    attempt to render itself centered on the Y position and placed to
    the right of X."""
    self.x = x
    self.y = y
    self.entity = entity

  def render(self, console):
    """ For this basic implementation we will just render the items name """
    pass
