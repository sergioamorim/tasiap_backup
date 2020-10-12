from contextlib import contextmanager
from pathlib import PurePath

from paramiko import SSHClient


@contextmanager
def open_ssh_session(client_options, credentials):
  ssh = active_ssh_session(
    ssh=setup_client(client_options=client_options),
    credentials=credentials
  )
  try:
    yield ssh
  finally:
    close_ssh_session(ssh=ssh)


def active_ssh_session(ssh, credentials):
  ssh.connect(
    username=credentials['username'],
    hostname=credentials['hostname'],
    port=credentials['port'],
    pkey=credentials['pkey']
  )
  return ssh


def setup_client(client_options):
  ssh = SSHClient()
  ssh.load_host_keys(filename=client_options['hosts_keys_filename'])
  return ssh


def close_ssh_session(ssh):
  ssh.exec_command(command='quit')
  ssh.close()


def localpath(filename, backups_directory):
  return PurePath('{backups_directory}/{filename}'.format(
    backups_directory=backups_directory,
    filename=filename
  ))
