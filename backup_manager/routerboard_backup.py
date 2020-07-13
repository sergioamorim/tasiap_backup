from datetime import datetime

import config
from backup_manager.ssh_client import supply_ssh_connection


def make_filename(prefix):
  return '{prefix}_{current_datetime}'.format(prefix=prefix, current_datetime=current_datetime())


def current_datetime():
  return datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def make_backup_filename(device_id):
  filename = make_filename(prefix=device_id)
  return '{filename}.backup'.format(filename=filename)


def make_script_filename(device_id):
  filename = make_filename(prefix=device_id)
  return '{filename}.rsc'.format(filename=filename)


def make_backup_command(device_id):
  filename = make_backup_filename(device_id=device_id)
  return {
    'command': str(
      '/system backup save name={filename} password={backup_password}'
    ).format(filename=filename, backup_password=config.backup_password),
    'filename': filename,
  }


def make_export_command(device_id):
  filename = make_script_filename(device_id=device_id)
  return {
    'command': '/ export file={filename}'.format(filename=filename),
    'filename': filename,
  }


def make_delete_file_command(filename):
  return '/file remove {filename}'.format(filename=filename)


@supply_ssh_connection
def generate_backup(device_id, ssh=None):
  backup_command = make_backup_command(device_id=device_id)
  ssh.exec_command(command=backup_command['command'])
  return backup_command['filename']


def make_localpath(filename):
  return '{backup_files_directory_path}/{filename}'.format(
    backup_files_directory_path=config.backup_files_directory_path,
    filename=filename
  )


def make_remotepath(filename):
  return '/{filename}'.format(filename=filename)


def retrieve_file(filename, sftp):
  remotepath = make_remotepath(filename=filename)
  localpath = make_localpath(filename=filename)
  sftp.get(remotepath=remotepath, localpath=localpath)
  return localpath


def delete_remote_file(filename, sftp):
  remotepath = make_remotepath(filename=filename)
  sftp.unlink(path=remotepath)


def clean_remote_backup_files(filenames, sftp):
  for filename in filenames:
    delete_remote_file(filename=filename, sftp=sftp)


def retrieve_backup_files(filenames, sftp):
  return [retrieve_file(filename=filename, sftp=sftp) for filename in filenames]
