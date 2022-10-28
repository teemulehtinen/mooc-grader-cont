import os
import docker

IMAGE = 'teemule/flask'

docker_client = docker.from_env()

def remove_dir(dir_path):
  if os.path.exists(dir_path):
    docker_client.containers.run(
      IMAGE,
      f'/bin/rm -rf /wdir/{os.path.basename(dir_path)}',
      volumes = {
        os.path.dirname(os.path.abspath(dir_path)): {'bind': '/wdir', 'mode': 'rw'}
      },
      remove = True,
    )

def ensure_network(name, create=True):
  nets = list(n for n in docker_client.networks.list() if n.name == name)
  if len(nets) > 0:
    return nets[0]
  if create:
    return docker_client.networks.create(name)
  return None

def get_container(name):
  try:
    c = docker_client.containers.get(name)
    if c.status != 'exited':
      return c
    c.remove()
  except docker.errors.NotFound:
    pass
  return None

def ensure_receiver(name, host, network):
  receiver = get_container(name)
  if not receiver:
    net = ensure_network(network)
    receiver = docker_client.containers.run(
      IMAGE,
      name=name,
      remove=True,
      detach=True,
      stdin_open=True,
      tty=True,
      ports={5000: 5000},
    )
    net.connect(receiver, aliases=[host])
  return receiver

def cleanup_network(network):
  for c in docker_client.containers.list(filters={'network': network}):
    c.kill()
  net = ensure_network(network)
  if net:
    net.remove()
