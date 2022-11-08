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
  copied = set()
  to_fill = [(e['name'], e['name']) for e in config.get('fields', [])]
  to_fill.extend((e['field'], e['name']) for e in config.get('files', []))

  # Support test LTI parameters
  if 'lti' in config:
    to_fill.append(('lti', 'lti.json'))

  # Find content from values or files
  for key, file in to_fill:
    v = values.get(key) or values.get(file)
    if not v is None:
      write_text_file(dir_path, file, v)
      filled.add(key)
    else:
      for p in file_paths:
        if os.path.basename(p) == file:
          shutil.copy(p, os.path.join(dir_path, file), follow_symlinks=True)
          filled.add(key)
          copied.add(p)

  # Use remaining files for any missing content
  for key, file in to_fill:
    if not key in filled:
      for p in file_paths:
        if not p in copied:
          shutil.copy(p, os.path.join(dir_path, file), follow_symlinks=True)
          filled.add(key)
          copied.add(p)

  # Report missing content
  return list(
    f'{key}:{file}' if key != file else key
    for key, file in to_fill if not key in filled
  )
