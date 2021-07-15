import lzma
import pickle
import os
from sectors import SectorTemplate


class CreatorEngine:
  def __init__(self, sector_width, sector_height):
    self.sector_width = sector_width
    self.sector_height=sector_height
    #self.message_log = MessageLog()
    self.mouse_location = (0,0)
    try:
      with open(f'sectors_{sector_width}x{sector_height}.dat', 'rb') as f:
        print('Loading sectors...')
        self.sectors = pickle.loads(lzma.decompress(f.read()))
        print('...loaded %s sectors' % (len(self.sectors)))
    except FileNotFoundError:
      print('No sectors found to load.')
      self.sectors = []

    self.current_sector = None

  def load_sector(self, index):
    self.current_sector = self.sectors[index]

  def delete_sector(self):
    self.sectors.remove(self.current_sector)
    self.current_sector = None

  def new_sector(self, name):
    self.current_sector = SectorTemplate(self.sector_width, self.sector_height, name)
    self.sectors.append(self.current_sector)


  def save_sectors(self):
    save_data = lzma.compress(pickle.dumps(self.sectors))
    with open(f'sectors_{self.sector_width}x{self.sector_height}.dat', 'wb') as f:
      f.write(save_data)
