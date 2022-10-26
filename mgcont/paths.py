import os

def scan_file_paths(dir_path):
  for path in os.scandir(dir_path):
      if path.is_file():
          yield path.name

def search_upwards(start_file_path, contained_dir_path):
  p = os.path.dirname(os.path.abspath(start_file_path))
  while p:
    if os.path.isdir(os.path.join(p, contained_dir_path)):
      return p
    p = os.path.dirname(p)
  return None
