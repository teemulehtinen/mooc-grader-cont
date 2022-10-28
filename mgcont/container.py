import os


class ContainerError(Exception):
  pass


def check_container_configuration(exercise_config):
  c_config = exercise_config.get('container')
  if not c_config:
    raise ContainerError(f'Configuration does not specify a "container" for asynchronous grading')
  
  # Check required keys
  for k in ('image', 'mount', 'cmd'):
    if not k in c_config:
      raise ContainerError(f'Container configuration is missing a required key: {k}')

  # Check paths for optional mounts
  mounts = c_config.get('mounts')
  if mounts:
    if not isinstance(mounts, dict):
      raise ContainerError(
        'If container configuration provides "mounts", it must be an object that '
        'maps relative course paths to absolute mount paths inside the container'
      )
    for c_path, m_path in mounts.items():
      if not os.path.isabs(m_path):
        raise ContainerError(f'Mount path must be absolute: {m_path}')
      if os.path.isabs(c_path) or os.path.normpath(c_path).startswith('..'):
        raise ContainerError(
          f'Path to be mounted must be a relative path (to course root): {c_path}'
        )
      for p in ('/exercise', '/submission', '/personalized_exercise', '/bin', '/etc', '/usr'):
        if m_path == p or m_path.startswith(p + '/'):
          raise ContainerError('{p} is a reserved path that cannot be mounted in "mounts"')
    if len(set(mounts.values())) != len(mounts):
        raise ContainerError('Mount paths must be distinct')
  return c_config


def create_container(
  host_url,
  root_path,
  course,
  exercise,
  submission_id,
  dir_path,
  run_func,
  run_settings
):
  config = exercise['container']
  ro_mounts = config.get('mounts', {}).copy()
  ro_mounts[config['mount']] = '/exercise'
  ro_mounts = {
    os.path.join(root_path, c_path): m_path
    for c_path, m_path in ro_mounts.items()
  }
  #if exercise.get("personalized", False):
  #  personalized_dir = select_generated_exercise_instance(course, exercise, uids, attempt)
  #  ro_mounts[personalized_dir] = "/personalized_exercise"
  return run_func(
    course=course,
    exercise=exercise,
    container_config=config,
    submission_id=submission_id,
    host_url=host_url,
    readwrite_mounts={ dir_path: '/submission' },
    readonly_mounts=ro_mounts,
    image=config['image'],
    cmd=config['cmd'],
    settings=run_settings,
  )
