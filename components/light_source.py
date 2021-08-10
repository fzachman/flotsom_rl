from components.base_component import BaseComponent
import exceptions
import color


class LightSource(BaseComponent):
  def __init__(self, radius=5,tint=(0,0,0)):
    self.radius = radius
    self.tint   = tint
