from datetime import datetime
from pathlib import PurePath
from re import findall, match

from backup.ssh_client import localpath, open_ssh_session, open_sftp


class BackupFile:
  def __init__(self, filename, size):
    self.filename = filename
    self.size = size

  def __eq__(self, other):
    return (
      type(self) == type(other)
      and self.filename == other.filename
      and self.size == other.size
    )

  @property
  def size(self):
    return self.__size

  @size.setter
  def size(self, size):
    self.__size = int(size)

  @property
  def creation(self):
    if creation_string := self.creation_string_on_filename:
      return datetime.strptime(creation_string, '%Y-%m-%d-%H%M')
    return None

  @property
  def extension(self):
    if file_extension := findall(pattern='.*\\.(.*)', string=self.filename):
      return file_extension[0]
    return None

  def is_smaller_than(self, other):
    return self.size < other.size

  def is_newer_than(self, other):
    return self.creation > other.creation

  @property
  def creation_string_on_filename(self):
    if creation_string := findall(
      pattern='.*([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}).*',  # <year>-<month>-<day>-<hour><minute>
      string=self.filename
    ):
      return creation_string[0]
    return None


def are_not_corrupted(backup_files):
  if backup_files:
    return (
      not is_corrupted(backup_file=backup_files.pop(), backup_files=backup_files.copy())
      and are_not_corrupted(backup_files=backup_files)
    )

  return True


def is_smaller_than_older(backup_file, backup_files):
  if backup_files:
    return (
      (
        backup_file.is_newer_than(
          other=(other_backup_file := backup_files.pop())
        )
        and backup_file.is_smaller_than(other=other_backup_file)
      )
      or is_smaller_than_older(backup_file=backup_file, backup_files=backup_files)
    )

  return False


def is_corrupted(backup_file, backup_files):
  return (
    not backup_file.size
    or backup_file.extension != 'tgz'
    or is_smaller_than_older(backup_file=backup_file, backup_files=backup_files)
  )


def newest_backup(backup_files):
  return sorted(
    backup_files,
    key=lambda backup_file: backup_file.creation,
    reverse=True
  )[0] if backup_files else None


def disposable_backups(backup_files, keeping_quantity):
  return sorted(
    backup_files,
    key=lambda backup_file: backup_file.creation
  )[:len(backup_files) - keeping_quantity]


def backup_files_found(sftp_attributes_from_files):
  return [
    BackupFile(
      filename=sftp_attributes.filename,
      size=sftp_attributes.st_size
    ) for sftp_attributes in filter(
      lambda sftp_attributes: is_valid_backup_filename(filename=sftp_attributes.filename),
      sftp_attributes_from_files
    )
  ]


def is_valid_backup_filename(filename):
  return match(string=filename, pattern=r'backup.+\.+')


def retrieved_file(current_remotepath, current_localpath, sftp):
  sftp.get(remotepath=current_remotepath, localpath=current_localpath)
  return current_localpath


def remotepath(remote_directory, filename):
  return PurePath(
    '{remote_directory}{filename}'.format(
      remote_directory=remote_directory,
      filename=filename
    )
  )


def labeled_backups(backup_files, keeping_quantity):
  return {
    'newest_backup': newest_backup(backup_files=backup_files),
    'disposable_backups': disposable_backups(
      backup_files=backup_files,
      keeping_quantity=keeping_quantity
    )
  }


def deleted_remote_backup_files(remote_directory, backup_files, sftp):
  return [
    deleted_remote_file(
      file_remotepath=remotepath(
        remote_directory=remote_directory,
        filename=backup_file.filename),
      sftp=sftp
    ) for backup_file in backup_files
  ]


def deleted_remote_file(file_remotepath, sftp):
  sftp.unlink(path=file_remotepath)
  return file_remotepath


def retrieved_and_deleted_backups(current_labeled_backups, backup_settings, sftp):
  return {
    'retrieved_backup': retrieved_file(
      current_remotepath=remotepath(
        remote_directory=backup_settings['remote_backups_directory'],
        filename=current_labeled_backups['newest_backup']
      ),
      current_localpath=localpath(
        backups_directory=backup_settings['local_backups_directory'],
        filename=current_labeled_backups['newest_backup'].filename
      ),
      sftp=sftp
    ),
    'deleted_backups': deleted_remote_backup_files(
      remote_directory=backup_settings['remote_backups_directory'],
      backup_files=current_labeled_backups['disposable_backups'],
      sftp=sftp
    )
  }


def myauth_backup(myauth, ssh_client_options):
  with open_ssh_session(
    client_options=ssh_client_options,
    credentials=myauth['credentials']
  ) as ssh:
    with open_sftp(ssh=ssh) as sftp:
      return retrieved_and_deleted_backups(
        current_labeled_backups=labeled_backups(
          backup_files=backup_files_found(
            sftp_attributes_from_files=sftp.listdir_attr(
              path=myauth['backup_settings']['remote_backups_directory']
            )
          ),
          keeping_quantity=myauth['backup_settings']['keeping_backups_quantity']
        ),
        backup_settings=myauth['backup_settings'],
        sftp=sftp
      )
