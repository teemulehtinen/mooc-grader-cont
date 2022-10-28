# Orders a container using docker run command. Prerequisites:
# 1. Docker is installed on the computer.
# 2. Mooc-grader containers should post results to {host_url}/container-post
# 
# Optional settings:
#   network
#       The docker network where the container is started. To receive the
#       result posts the server (e.g. mooc-grader) has to be running inside
#       docker in the same network, alternatively linux docker can use
#       "host" for the host's network and run server without docker.
#       The receiving server must listen at all IP addresses on the machine
#       (e.g. runserver 0.0.0.0:8080).
#   mount
#       A dictionary to override or prefix mount source paths.
#   debug_mode 
#       True to support debugging (e.g. docker attach -it {name}) by running
#       shell instead of the configured command inside the container.
#
import logging
import os.path
from typing import Any, Dict, Tuple
import docker

docker_client = docker.from_env()

logger = logging.getLogger('runner.docker')

def run(
  submission_id: str,
  host_url: str,
  readwrite_mounts: Dict[str, str],
  readonly_mounts: Dict[str, str],
  image: str,
  cmd: str,
  settings: Dict[str, Any],
  **kwargs,
) -> Tuple[int, str, str]:
  """
  Grades the submission asynchronously and returns (return_code, std_out, std_err).
  """
  network = settings.get('network', 'bridge')
  host_mount_points = settings.get('mounts')
  debug_mode = settings.get('debug_mode', False)

  # Prepare to rewrite paths for the host
  def rewrite_path(path: str):
    path = os.path.realpath(path)
    for from_path, to_path in host_mount_points.items():
      if path.startswith(from_path):
        return path.replace(from_path, to_path)
    logger.error(f'Could not find where {path} is mounted')
    return path
  host_path = (lambda p: rewrite_path(p)) if host_mount_points else (lambda p: p)

  # Create volume mapping
  volumes = {
    host_path(s_path): {'bind': t_path, 'mode': 'rw'}
    for s_path, t_path in readwrite_mounts.items()
  }
  volumes.update({
    host_path(s_path): {'bind': t_path, 'mode': 'ro'}
    for s_path, t_path in readonly_mounts.items()
  })

  # Run container
  try:
    container = docker_client.containers.run(
      image,
      '/bin/bash' if debug_mode else cmd,
      network=network,
      remove=True,
      detach=True,
      stdin_open=debug_mode,
      tty=debug_mode,
      environment={'SID': submission_id, 'REC': host_url},
      volumes=volumes,
    )
    if debug_mode:
      logger.warning(
        'Running debug shell instead of the configured cmd. Attach to it with docker.\n'
        f'  cmd:     {cmd}\n'
        f'  shell:   docker attach {container.name}'
      )
    return 0, f'{", ".join(container.image.tags)} - {container.name} - {container.short_id}', ''
  except Exception as e:
      logger.exception('An exception while trying to run grading container')
      return 1, '', str(e)
