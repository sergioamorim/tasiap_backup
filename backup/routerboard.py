from datetime import datetime, timedelta
from pathlib import PurePath

from backup.ssh_client import open_ssh_session


class RemotePath:
  def __init__(self, path):
    self.pure = PurePath(path)

  @property
  def without_root(self):
    return remotepath_without_root(remotepath=self.pure)

  @property
  def parent_without_root(self):
    return remotepath_without_root(remotepath=self.pure.parent)


def make_filename(prefix):
  return '{prefix}_{current_datetime}'.format(prefix=prefix, current_datetime=current_datetime())


def current_datetime():
  return datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def backup_filename(device_id):
  return '{filename}.backup'.format(filename=make_filename(prefix=device_id))


def script_filename(device_id):
  return '{filename}.rsc'.format(filename=make_filename(prefix=device_id))


def backup_command(device_id, backup_password):
  filename = backup_filename(device_id=device_id)
  return {
    'command': str(
      '/system backup save name={filename} password={backup_password}'
    ).format(filename=filename, backup_password=backup_password),
    'filename': filename,
  }


def export_command(device_id):
  filename = script_filename(device_id=device_id)
  return {
    'command': '/ export file={filename}'.format(filename=filename),
    'filename': filename,
  }


def generate_backup(device_id, backup_password, ssh):
  current_backup_command = backup_command(device_id=device_id, backup_password=backup_password)
  ssh.exec_command(command=current_backup_command['command'])
  return current_backup_command['filename']


def generate_export_script(device_id, ssh):
  current_export_command = export_command(device_id=device_id)
  ssh.exec_command(command=current_export_command['command'])
  return current_export_command['filename']


def localpath(filename, backups_directory):
  return PurePath('{backups_directory}/{filename}'.format(
    backups_directory=backups_directory,
    filename=filename
  ))


def retrieve_file(filename, backups_directory, sftp):
  current_localpath = localpath(filename=filename, backups_directory=backups_directory)
  remotepath = RemotePath(path=filename)
  if assert_remote_file_exists(remotepath=remotepath, sftp=sftp):
    sftp.get(remotepath=remotepath.without_root, localpath=str(current_localpath))
    sftp.unlink(path=remotepath.without_root)
    return current_localpath
  return None


def retrieve_backup_files(filenames, backups_directory, sftp):
  return [retrieve_file(
    filename=filename,
    backups_directory=backups_directory,
    sftp=sftp
  ) for filename in filenames]


def backup(routerboard, backups_directory, ssh):
  return retrieve_backup_files(
    filenames=[
      generate_backup(
        device_id=routerboard['name'],
        backup_password=routerboard['backup_password'],
        ssh=ssh
      ),
      generate_export_script(device_id=routerboard['name'], ssh=ssh)
    ],
    backups_directory=backups_directory,
    sftp=ssh.open_sftp()
  )


def remote_file_exists(remotepath, sftp):
  return remotepath.pure.name in sftp.listdir(path=remotepath.parent_without_root)


def timeout(start_time, seconds):
  return datetime.now() >= start_time + timedelta(seconds=seconds)


def assert_remote_file_exists(remotepath, sftp, seconds=10):
  start_time = datetime.now()
  while (
    not remote_file_exists(remotepath=remotepath, sftp=sftp) and
    not timeout(start_time=start_time, seconds=seconds)
  ):
    pass

  return remote_file_exists(remotepath=remotepath, sftp=sftp)


def remotepath_without_root(remotepath):
  remotepath_str = str(remotepath)
  root = str(remotepath.root)
  return '.' if remotepath_str == root else remotepath_str.replace(root, '', 1).replace('\\', '/')


def routerboards_backups(routerboards, backups_directory, ssh_client_options):
  backups = []
  for routerboard in routerboards:
    with open_ssh_session(
      client_options=ssh_client_options,
      credentials=routerboard['credentials']
    ) as ssh:
      backups.append(backup(
        routerboard=routerboard,
        backups_directory=backups_directory,
        ssh=ssh
      ))
  return backups
