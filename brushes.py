import numpy as np

class Brush:
  def __init__(self, name, size=3, data = []):
    self.name = name
    self.size = int(size)
    if data:
      self.data = np.array(data, dtype=np.int16)
    else:
      self.data = np.full((self.size,self.size),fill_value=255, dtype=np.int16)

  def to_dict(self):
    return {'name': self.name,
            'size': self.size,
            'data': self.data.tolist()}

  def get_all_rotations(self):
    return (self.data,
             np.rot90(self.data).copy(),
             np.rot90(self.data,2).copy(),
             np.rot90(self.data,3).copy())

  def render(self, console, render_x, render_y):
    for x in range(self.size):
      for y in range(self.size):
        color = self.data[x,y]
        console.tiles_rgb['bg'][render_x + x,render_y + y] = (color,color,color)

  #def __eq__(self, other):
  #  if type(other) != type(self):
  #    raise TypeError(f'Cannot compare {type(self)} with {type(other)}')
  #
  #  return np.all(self.data == other.data)

class BrushSet:
  def __init__(self, name, brush_size=3):
    self.name = name
    self.brush_size = int(brush_size)
    self.brushes = {}

  def add_brush(self, brush, weight=1):
    if brush.size != self.brush_size:
      raise ValueError('Invalid brush size.  Expected size %s, got size %s' % (self.brush_size, brush.size))
    self.brushes[brush.name] = {'brush': brush,
                                'weight': int(weight)}

  def list_brushes(self):
    return self.brushes.values()

  def to_dict(self):
    brushes = []
    for n, b in self.brushes.items():
      brush = {'brush_name': b['brush'].name,
               'weight': b['weight']}
      brushes.append(brush)

    return {'name': self.name,
            'brush_size': self.brush_size,
            'brushes': brushes}
