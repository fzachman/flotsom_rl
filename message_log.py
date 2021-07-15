import textwrap
import tcod
import color

class Message:
  def __init__(self, text, fg):
    self.plain_text = text
    self.fg = fg
    self.count = 1

  @property
  def full_text(self):
    """The full text of this message, including the count if necessary."""
    if self.count > 1:
      return f"{self.plain_text} (x{self.count})"
    return self.plain_text


class MessageLog:
  def __init__(self):
    self.messages = []

  def add_message(
      self, text, fg = color.white, *, stack = True,
  ):
    """Add a message to this log.
    `text` is the message text, `fg` is the text color.
    If `stack` is True then the message can stack with a previous message
    of the same text.
    """
    if stack and self.messages and text == self.messages[-1].plain_text:
      self.messages[-1].count += 1
    else:
      self.messages.append(Message(text, fg))

  def render(
      self, console, x, y, width, height,
  ):
    """Render this log over the given area.
    `x`, `y`, `width`, `height` is the rectangular region to render onto
    the `console`.
    """
    self.render_messages(console, x, y, width, height, self.messages)

  @staticmethod
  def wrap(string, width):
    """ Return a wrapped text message """
    for line in string.splitlines(): # Handle newlines in messages
      yield from textwrap.wrap(line, width, expand_tabs=True)

  @classmethod
  def render_messages(
      cls,
      console,
      x,
      y,
      width,
      height,
      messages,
  ):
    """Render the messages provided.
    The `messages` are rendered starting at the last message and working
    backwards.
    """
    y_offset = height - 1

    for message in reversed(messages):
      for line in reversed(list(cls.wrap(message.full_text, width))):
        console.print(x=x, y=y + y_offset, string=line, fg=message.fg)
        y_offset -= 1
        if y_offset < 0:
          return  # No more space to print messages.
