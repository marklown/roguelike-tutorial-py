
class Impossible(Exception):
  """Exception raised when an action is impossible to perform"""

class QuitWithoutSaving(SystemExit):
  """Can be raised to exit the game without automatically saving"""