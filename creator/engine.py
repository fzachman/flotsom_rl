import lzma
import pickle
import os
import json
from message_log import MessageLog
from brushes import Brush, BrushSet
from exceptions import DuplicateNameException


class CreatorEngine:
  def __init__(self):
    self.message_log = MessageLog()
    self.mouse_location = (0,0)
    self.brushes = {}
    self.brushes_by_size = {}
    self.brush_sets = {}
    self.current_brush_set = None
    self.is_enemy_turn = False
    self.load_brushes('brushes.json')

  def orbit(self):
    pass

  def load_brushes(self, filename='brushes.json'):
    try:
      with open(filename, 'r') as f:
        data = json.loads(f.read())
        for b in data.get('brushes', []):
          brush = Brush(b['name'],size=b['size'],data=b['data'])
          self.brushes[brush.name] = brush
          self.brushes_by_size.setdefault(brush.size, []).append(brush)
        for s in data.get('brush_sets'):
          brush_set = BrushSet(s['name'],s['brush_size'])
          for b in s.get('brushes', []):
            brush = self.brushes.get(b['brush_name'])
            if brush:
              brush_set.add_brush(brush, b['weight'])
          self.brush_sets[brush_set.name] = brush_set
      print(self.brushes)
    except FileNotFoundError:
      self.message_log.add_message('No brush data found.')


  def save_brushes(self, filename='brushes.json'):
    brush_data = []
    brush_set_data = []
    for b in self.brushes.values():
      brush_data.append(b.to_dict())
    for s in self.brush_sets.values():
      brush_set_data.append(s.to_dict())
    data = {'brushes': brush_data,
            'brush_sets': brush_set_data}
    data = json.dumps(data)
    with open(filename, 'w') as f:
      f.write(data)

    self.message_log.add_message('Brush data saved.')

  def list_brushes(self, size=None):
    if size == None:
      brushes = [(brush.name, brush) for brush in self.brushes.values()]
    else:
      brushes = [(brush.name, brush) for brush in self.brushes_by_size.get(size, [])]
    brushes.sort()
    return [b for s,b in brushes]

  def list_brush_sets(self):
    brush_sets = [(s.name, s) for s in self.brush_sets.values()]
    brush_sets.sort()
    return [s for n,s in brush_sets]


  def delete_brush(self, brush):
    try:
      del(self.brushes[brush.name])
    except KeyError:
      self.message_log.add_message('Invalid brush name: %s' % brush_name)
    self.current_brush = None

  def delete_brush_set(self, set_name):
    brush_set = self.current_brush_set
    try:
      del(self.brush_sets[brush_set.name])
    except KeyError:
      self.message_log.add_message('Invalid brush set name: %s' % set_name)
    self.current_brush_set = None

  def new_brush(self, name, size):
    if name in self.brushes:
      raise DuplicateNameExceptions('A brush with that name already exists.')
    size = int(size)
    brush = Brush(name, size)
    self.brushes[name] = brush
    return brush

  def new_brush_set(self, name, brush_size):
    if name in self.brush_sets:
      raise DuplicateNameExceptions('A brush set with that name already exists.')

    self.current_brush_set = BrushSet(name, brush_size)
    self.brush_sets[name] = self.current_brush_set


  def render(self, console):
    self.message_log.render(console=console,x=console.height-5,y=0,width=console.width,height=5)
