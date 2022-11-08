import argparse
import json
import os
import sys
import yaml

from .container import ContainerError, check_container_configuration, create_container
from .docker_utils import cleanup_network, ensure_receiver, remove_dir
from .docker_run import run as run_docker_container
from .paths import scan_file_paths, search_upwards
from .submission_dir import build_submission_dir

TMP_DIR = 'submission_tmp'
NETWORK = 'mgcont'
REC_NAME = 'mgcont_receiver'
REC_HOST = 'debugger'
REC_URL = f'http://{REC_HOST}:5000'
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
  parser = argparse.ArgumentParser(description=(
    'Constructs and runs grading containers to test exercises for mooc-grader. '
    f'Use "docker attach {REC_NAME}" to view grading results.'
  ))
  parser.add_argument('--receiver', action='store_true', default=False,
    help='only start the receiver')
  parser.add_argument('--cleanup', action='store_true', default=False,
    help='remove any remaining containers and temporary files')
  parser.add_argument('-c', '--config', help='a mooc-grader exercise configuration yaml/json')
  parser.add_argument('-f', '--file', nargs='+', help='a file to submit')
  parser.add_argument('-d', '--dir', help='a directory including the files to submit')
  parser.add_argument('--values',
    help='a yaml/json file to use as posted values or file contents')
  parser.add_argument('--debug', action='store_true', default=False,
    help='run a debug shell instead of the configured grading command')
  args = parser.parse_args()
  
  # Clean-up
  if args.cleanup:
    cleanup_network(NETWORK)
    remove_dir(TMP_DIR)
    sys.exit(0)

  # Start receiver
  ensure_receiver(REC_NAME, REC_HOST, NETWORK)
  if args.receiver:
    print(f'View with: docker attach {REC_NAME}')
    sys.exit(0)

  # Handle arguments
  if not args.config:
    exit(
      'An exercise configuration file (-c FILE or --config FILE) is required.\n'
      'Use -h or --help for more instructions.'
    )
  config = read_config(args.config)
  values = read_config(args.values) if args.values else {}
  if not isinstance(values, dict):
    exit(f'Values must be declared as an object.')
  files = []
  for f in args.file or []:
    if not os.path.isfile(f):
      exit(f'No such file found: {f}')
    files.append(f)
  if args.dir:
    if not os.path.isdir(args.dir):
      exit(f'No such directory found: {args.dir}')
    files.extend(scan_file_paths(args.dir))

  # Construct submission-directory
  remove_dir(TMP_DIR)
  missing = build_submission_dir(TMP_DIR, config, values, files)
  if missing:
    print(f'Warning, following configured values are missing: {" ".join(missing)}')

  # Run the configured container with the configured mounts
  try:
    check_container_configuration(config)
    root_path = search_upwards(args.config, config['container']['mount'])
    if root_path is None:
      exit(f'Failed to find a root directory containing the configuration and the "mount" directory.')
    exi, out, err = create_container(
      host_url=REC_URL,
      root_path=root_path,
      course={},
      exercise=config,
      submission_id='debugsubmission',
      dir_path=os.path.abspath(TMP_DIR),
      run_func=RUN_FUNC,
      run_settings={'network': NETWORK, 'debug_mode': args.debug}
    )
    if exi != 0:
      exit(f'Failed to run container:\n{err}')
  except ContainerError as e:
    exit(e.message)
