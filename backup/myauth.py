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
    return datetime.strptime(self.filename, 'backup-%Y-%m-%d-%H%M.tgz')

  @property
  def extension(self):
    if file_extension := findall(pattern='.*\\.(.*)', string=self.filename):
      return file_extension[0]
    return None

  def is_bigger_than(self, other):
    return self.size > other.size

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
