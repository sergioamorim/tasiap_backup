from datetime import datetime
from unittest import TestCase

from backup.myauth import BackupFile, are_not_corrupted


class TestBackupFileClass(TestCase):

  def setUp(self):
    self.filename = 'backup-2020-08-08-0440.tgz'
    self.size = '261706551'
    self.backup_file = BackupFile(filename=self.filename, size=self.size)

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

  def test_is_smaller_than(self):
    self.assertFalse(
      expr=self.backup_file.is_smaller_than(
        other=BackupFile(
          filename='backup-2020-08-08-0440.tgz',
          size=self.backup_file.size - 1
        )
      ),
      msg='Returns False when it is bigger than the backup file passed'
    )

    self.assertFalse(
      expr=self.backup_file.is_smaller_than(
        other=BackupFile(
          filename='backup-2020-08-08-0441.tgz',
          size=self.backup_file.size
        )
      ),
      msg='Returns False when it has the same size of the backup file passed'
    )

    self.assertTrue(
      expr=self.backup_file.is_smaller_than(
        other=BackupFile(
          filename='backup-2020-08-08-0442.tgz',
          size=self.backup_file.size + 1
        )
      ),
      msg='Returns True when it is smaller than the backup file passed'
    )

  def test_is_newer_than(self):
    other = BackupFile(filename='backup-2020-08-08-0440.tgz', size=1)

    self.backup_file.filename = 'backup-2020-08-08-0439.tgz'
    self.assertFalse(
      expr=self.backup_file.is_newer_than(other=other),
      msg='Returns False when it is not newer than the backup file passed'
    )

    self.backup_file.filename = 'backup-2020-08-08-0440.tgz'
    self.assertFalse(
      expr=self.backup_file.is_newer_than(other=other),
      msg='Returns False when it has the same creation time than the backup file passed'
    )

    self.backup_file.filename = 'backup-2020-08-08-0441.tgz'
    self.assertTrue(
      expr=self.backup_file.is_newer_than(other=other),
      msg='Returns True when it is newer than the backup file passed'
    )

  def test_creation_string_on_filename(self):
    self.backup_file.filename = 'backup-today.tgz'
    self.assertIsNone(
      obj=self.backup_file.creation_string_on_filename,
      msg='Returns None when the filename has not a inner string with the format <year>-<month>-<day>-<hour><minute>'
    )

    self.backup_file.filename = 'backup-2020-08-08-0440.tgz'
    self.assertEqual(
      first='2020-08-08-0440',
      second=self.backup_file.creation_string_on_filename,
      msg='Returns the string related to the creation of the file on the its filename'
    )

  def test_extension(self):
    self.backup_file.filename = 'backup'
    self.assertIsNone(
      obj=self.backup_file.extension,
      msg='Returns None when the filename has not a extension explicitly defined'
    )

    self.backup_file.filename = 'backup.tgz'
    self.assertEqual(
      first='tgz',
      second=self.backup_file.extension,
      msg='Returns the extension of the file explicitly defined in the filename'
    )

    self.backup_file.filename = 'backup.tar.gz'
    self.assertEqual(
      first='gz',
      second=self.backup_file.extension,
      msg='Returns only the last extension of the file explicitly defined in the filename'
    )

  def test_creation(self):
    self.assertEqual(
      first=datetime.strptime(self.backup_file.creation_string_on_filename, '%Y-%m-%d-%H%M'),
      second=self.backup_file.creation,
      msg='Returns a datetime from the time and date written in the filename'
    )

    self.backup_file.filename = 'different-name-format-with-2020-08-23-0445-the-date-and-time-written-in-it'
    self.assertEqual(
      first=datetime.strptime(self.backup_file.creation_string_on_filename, '%Y-%m-%d-%H%M'),
      second=self.backup_file.creation,
      msg='Returns a datetime from the time and date written in the filename even with an unusual filename format'
    )

    self.backup_file.filename = 'filename-without-date-and-time'
    self.assertIsNone(
      obj=self.backup_file.creation,
      msg='Returns None when the filename does not have a date and time written in it'
    )


class TestMyauthFunctions(TestCase):

  def test_are_not_corrupted(self):
    self.assertTrue(
      expr=are_not_corrupted(backup_files=[]),
      msg='Returns True when the list of files is empty'
    )
    self.assertTrue(
      expr=are_not_corrupted(backup_files=[BackupFile(
        filename='backup-2020-08-23-0446.tgz',
        size='1'
      )]),
      msg='Returns True when the list contains at least one BackupFile with a valid filename and size'
    )
    self.assertFalse(
      expr=are_not_corrupted(backup_files=[
        BackupFile(
          filename='backup-2020-08-23-0448.tgz',
          size='1'
        ),
        BackupFile(
          filename='backup-2020-08-23-0447.tgz',
          size='0'
        )
      ]),
      msg="Returns False when one of the BackupFile's in the list has size 0"
    )
    self.assertFalse(
      expr=are_not_corrupted(backup_files=[
        BackupFile(
          filename='backup-2020-08-23-0446.tgz',
          size='1'
        ),
        BackupFile(
          filename='backup-2020-08-23-0447.tgz',
          size='2'
        ),
        BackupFile(
          filename='backup-2020-08-23-0448.tgz',
          size='1'
        ),
        BackupFile(
          filename='backup-2020-08-23-0449.tgz',
          size='4'
        )
      ]),
      msg="Returns False when one of the BackupFile's in the list is newer than another yet is smaller than this other"
    )

    self.assertTrue(
      expr=are_not_corrupted(backup_files=[
        BackupFile(
          filename='backup-2020-08-23-0446.tgz',
          size='1'
        ),
        BackupFile(
          filename='backup-2020-08-23-0447.tgz',
          size='2'
        ),
        BackupFile(
          filename='backup-2020-08-23-0448.tgz',
          size='2'
        ),
        BackupFile(
          filename='backup-2020-08-23-0449.tgz',
          size='4'
        )
      ]),
      msg="Returns True when the BackupFile's that are newer are bigger (or equal in size) too"
    )
