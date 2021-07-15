class BaseComponent:
  @property
  def gamemap(self):
    return self.parent.gamemap

  @property
  def engine(self):
    return self.gamemap.engine
