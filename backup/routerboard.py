from datetime import datetime, timedelta
from pathlib import PurePath

import config


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


def backup_command(device_id):
  filename = backup_filename(device_id=device_id)
  return {
    'command': str(
      '/system backup save name={filename} password={backup_password}'
    ).format(filename=filename, backup_password=config.backup_password),
    'filename': filename,
  }


def export_command(device_id):
  filename = script_filename(device_id=device_id)
  return {
    'command': '/ export file={filename}'.format(filename=filename),
    'filename': filename,
  }


def generate_backup(device_id, ssh):
  return generate_remotely(device_id=device_id, command_maker=backup_command, ssh=ssh)


def generate_remotely(device_id, command_maker, ssh):
  command_made = command_maker(device_id=device_id)
  ssh.exec_command(command=command_made['command'])
  return command_made['filename']


def generate_export_script(device_id, ssh):
  return generate_remotely(device_id=device_id, command_maker=export_command, ssh=ssh)


def localpath(filename):
  return PurePath('{backup_files_directory_path}/{filename}'.format(
    backup_files_directory_path=config.backup_files_directory_path,
    filename=filename
  ))


def retrieve_file(filename, sftp):
  current_localpath = localpath(filename=filename)
  remotepath = RemotePath(path=filename)
  if assert_remote_file_exists(remotepath=remotepath, sftp=sftp):
    sftp.get(remotepath=remotepath.without_root, localpath=str(current_localpath))
    sftp.unlink(path=remotepath.without_root)
    return current_localpath
  return None


def retrieve_backup_files(filenames, sftp):
  return [retrieve_file(filename=filename, sftp=sftp) for filename in filenames]


def backup(device_id, ssh):
  return retrieve_backup_files(
    filenames=[generate_backup(device_id=device_id, ssh=ssh), generate_export_script(device_id=device_id, ssh=ssh)],
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
