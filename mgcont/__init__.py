import argparse
import json
import os
import sys
import yaml

from .container import ContainerError, check_container_configuration, create_container
from .docker_run import run as run_docker_container
from .paths import scan_file_paths, search_upwards
from .submission_dir import build_submission_dir

RUN_FUNC = run_docker_container
CONFIG_LOADERS = {
  '.json': json.load,
  '.yaml': yaml.safe_load,
}

def exit(message):
  print(message)
  sys.exit(1)

def read_config(path):
  if not os.path.isfile(path):
    exit(f"No such file found: {path}")
  ext = os.path.splitext(path)[1]
  reader = CONFIG_LOADERS.get(ext)
  if not reader:
    exit(f"Configuration file has an unrecognixed extension ({ext}): {path}")
  with open(path, 'r') as f:
    return reader(f)

def main():
  parser = argparse.ArgumentParser(description='Start a grading container for testing')
  parser.add_argument('CONFIG', help='A mooc-grader exercise configuration yaml/json')
  parser.add_argument('--values', help=(
    'A yaml/json file to use as posted values, '
    '"meta" can be defined to simulate server provided meta-data'
  ))
  parser.add_argument('--file', help='A file to submit')
  parser.add_argument('--dir', help='A directory including the files to submit')
  parser.add_argument('--debug', action='store_true', default=False,
    help='Run a debug shell instead of the configured grading command')
  parser.add_argument('--network', default='mgcont',
    help='A network setting for docker run, e.g. mgcont (named docker network)')
  parser.add_argument('--rec', default='http://debugger:5000',
    help='An URL to the host to receive grading, e.g. http://debugger:5000')
  parser.add_argument('--grade-dir', default='./submission_tmp',
    help='A path where the grading mount is created, e.g. ./submission_tmp')
  args = parser.parse_args()
  
  # Handle arguments
  config = read_config(args.CONFIG)
  values = read_config(args.values) if args.values else {}
  if not isinstance(values, dict):
    exit(f"Values must be declared as an object")
  files = []
  if args.file:
    if not os.path.isfile(args.file):
      exit(f"No such file found: {args.file}")
    files.append(args.file)
  if args.dir:
    if not os.path.isdir(args.dir):
      exit(f"No such directory found: {args.dir}")
    files.extend(scan_file_paths(args.dir))

  # Construct submission-directory
  missing = build_submission_dir(args.grade_dir, config, values, files)
  if missing:
    print(f'Warning, following configured values are missing: {" ".join(missing)}')

  # Run the configured container with the configured mounts
  try:
    check_container_configuration(config)
    root_path = search_upwards(args.CONFIG, config['container']['mount'])
    if root_path is None:
      exit(f'Failed to find a root directory containing the configuration and the "mount" directory')
    ex, out, err = create_container(
      host_url=args.rec,
      root_path=root_path,
      course={},
      exercise=config,
      submission_id='debugsubmission',
      dir_path=os.path.abspath(args.grade_dir),
      run_func=RUN_FUNC,
      run_settings={'network': args.network, 'debug_mode': args.debug}
    )
    if ex == 0:
      name = out.split(' - ')[1]
      print(name)
    else:
      exit(f'Failed to run container:\n{err}')
  except ContainerError as e:
    exit(e.message)
