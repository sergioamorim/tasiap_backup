from datetime import datetime
from unittest import TestCase

from backup.myauth import BackupFile


class TestBackupFileClass(TestCase):

  @classmethod
  def setUpClass(cls):
    cls.filename = 'backup-2020-08-08-0440.tgz'
    cls.size = '261706551'
    cls.backup_file = BackupFile(filename=cls.filename, size=cls.size)

  def test_init(self):
    self.assertEqual(
      first=self.filename,
      second=self.backup_file.filename,
      msg='The filename passed is put into the filename attribute'
    )
    self.assertEqual(
      first=int(self.size),
      second=self.backup_file.size,
      msg='The size passed is put into the size attribute as integer'
    )
    self.assertEqual(
      first=datetime(year=2020, month=8, day=8, hour=4, minute=40),
      second=self.backup_file.creation,
      msg='Has a creation property that refers to the date and time written in the filename'
    )
    self.assertEqual(
      first='tgz',
      second=self.backup_file.extension,
      msg='Has an extension property referring to the extension of the file written in the filename'
    )

  def test_size(self):
    size = 1
    self.backup_file.size = size
    self.assertEqual(
      first=size,
      second=self.backup_file.size,
      msg='Sets the size to the size passed if it is an integer'
    )

    self.backup_file.size = str(++size)
    self.assertEqual(
      first=size,
      second=self.backup_file.size,
      msg='Sets the size to the integer version of the size passed if it is an string'
    )
