import json
import os
import shutil
import docker

def write_text_file(dir_path, file_name, content):
  with open(os.path.join(dir_path, file_name), 'w') as f:
    if isinstance(content, dict) or isinstance(content, list):
      f.write(json.dumps(content))
    else:
      f.write(str(content))

def build_submission_dir(dir_path, config, values, file_paths):
  os.makedirs(dir_path)
  filled = set()

  # Save expected and provided field values as files
  for e in config.get('fields', []):
    v = values.get(e['name'])
    if not v is None and not e['name'] in filled:
      write_text_file(dir_path, e['name'], v)
      filled.add(e['name'])

  # Support file contents from configured values
  for e in config.get('files', []):
    v = values.get(e['field']) or values.get(e['name'])
    if v and not e['field'] in filled:
      write_text_file(dir_path, e['name'], v)
      filled.add(e['field'])
  
  # Map provided to expected files, first by name, then any remaining
  files_map = {}
  def map_files(is_match):
    for e in config.get('files', []):
      if not e['field'] in filled:
        for p in file_paths:
          if not p in files_map.values() and is_match(p, e):
            files_map[e['name']] = p
            filled.add(e['field'])
  map_files(lambda p, e: os.path.basename(p) == e['name'])
  map_files(lambda _p, _e: True)
  for name, src in files_map.items():
    shutil.copy(src, os.path.join(dir_path, name), follow_symlinks=True)

  # Check missing data
  missing = []
  for e in config.get('fields', []):
    if not e['name'] in filled and e.get('required', False):
      missing.append(e['name'])
  for e in config.get('files', []):
    if not e['field'] in filled and e.get('required', True):
      missing.append(f'{e["field"]}:{e["name"]}')
  return missing
