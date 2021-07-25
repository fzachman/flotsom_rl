class Impossible(Exception):
  """Exception raised when an action is impossible to be performed.

  The reason is given as the exception message."""

class QuitWithoutSaving(SystemExit):
  """ Can be raised to exit the game without automatically saving"""

class DuplicateNameException(Exception):
  """ Raised by the creator when you add a brush/set with the same name as another """
