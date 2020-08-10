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
    return findall(pattern='.*\\.(.*)', string=self.filename)[0]
