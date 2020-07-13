from contextlib import contextmanager
from functools import wraps

from paramiko import SSHClient

import config


def supply_ssh_connection(function):
  @wraps(function)
  def supply_ssh_connection_wrapper(*args, **kwargs):
    if 'ssh' not in kwargs:
      with open_ssh_client(ssh_client_options=config.ssh_client_options, ssh_credentials=config.ssh_credentials) as ssh:
        return function(*args, **kwargs, ssh=ssh)

    return function(*args, **kwargs)

  return supply_ssh_connection_wrapper


@contextmanager
def open_ssh_client(ssh_client_options, ssh_credentials):
  ssh = setup_client(ssh_client_options=ssh_client_options)

  ssh.connect(
    username=ssh_credentials['username'],
    hostname=ssh_credentials['hostname'],
    port=ssh_credentials['port'],
    pkey=ssh_credentials['pkey']
  )

  try:
    yield ssh
  finally:
    close_connection(ssh=ssh)


def setup_client(ssh_client_options):
  ssh = SSHClient()
  ssh.load_host_keys(filename=ssh_client_options['hosts_keys_filename'])
  return ssh


def close_connection(ssh):
  ssh.exec_command(command='quit')
  ssh.close()
