from datetime import datetime
from re import findall


class BackupFile:
  def __init__(self, filename, size):
    self.filename = filename
    self.size = size

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
