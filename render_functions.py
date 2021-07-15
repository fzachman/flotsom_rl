import color

def get_names_at_location(x, y, game_map):
  if not game_map.in_bounds(x,y) or not game_map.visible[x,y]:
    return ''
  names = ', '.join(entity.name for entity in game_map.entities if entity.x == x and entity.y == y)
  return names.capitalize()

def render_bar(console,
               current_value,
               maximum_value,
               total_width,):
  bar_width = int(float(current_value) / maximum_value * total_width)
  console.draw_rect(x=0,y=45,width=20,height=1,ch=1,bg=color.bar_empty)

  if bar_width > 0:
    console.draw_rect(x=0,y=45,width=bar_width,height=1,ch=1,bg=color.bar_filled)

  console.print(x=1,y=45,string=f'HP: {current_value}/{maximum_value}', fg=color.bar_text)

def render_dungeon_level(console, dungeon_level, location):
  """Render the level the player is currently on, at the given location"""
  x,y = location
  console.print(x=x,y=y,string=f'Dungeon level: {dungeon_level}')

def render_names_at_mouse_location(console, x, y, engine):
  mouse_x, mouse_y = engine.mouse_location
  names_at_mouse_location = get_names_at_location(x=mouse_x,y=mouse_y,game_map=engine.game_map)
  console.print(x=x,y=y, string=names_at_mouse_location)
