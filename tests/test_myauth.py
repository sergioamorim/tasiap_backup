from datetime import datetime
from pathlib import PurePath
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from backup.myauth import BackupFile, are_not_corrupted, is_corrupted, is_smaller_than_older, newest_backup, \
  disposable_backups, backup_files_found, is_valid_backup_filename, retrieved_file, remotepath, labeled_backups, \
  retrieved_and_deleted_backups, deleted_remote_backup_files, deleted_remote_file, myauth_backup


class SFTPAttributesMock:
  def __init__(self, filename, st_size):
    self.filename = filename
    self.st_size = st_size


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

  def test_eq(self):
    self.assertNotEqual(
      first='',
      second=self.backup_file,
      msg='Can be compared to a different type of object but is not equal'
    )
    self.assertNotEqual(
      first=BackupFile(
        filename=self.backup_file.filename + '_different_filename',
        size=self.backup_file.size
      ),
      second=self.backup_file,
      msg='When the filename is different it is not equal'
    )
    self.assertNotEqual(
      first=BackupFile(
        filename=self.backup_file.filename,
        size=self.backup_file.size + 1
      ),
      second=self.backup_file,
      msg='When the size is different it is not equal'
    )
    self.assertEqual(
      first=BackupFile(
        filename=self.backup_file.filename,
        size=self.backup_file.size
      ),
      second=self.backup_file,
      msg='When it has the same filename and size it can be treated as equal'
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
        ),
        BackupFile(
          filename='backup-2020-08-23-0449.tgz',
          size='2'
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

    self.assertFalse(
      expr=are_not_corrupted(backup_files=[
        BackupFile(
          filename='backup-2020-08-23-0448.tgz',
          size='1'
        ),
        BackupFile(
          filename='backup-2020-08-23-0449.tar.gz',
          size='2'
        ),
        BackupFile(
          filename='backup-2020-08-23-0447.tgz',
          size='1'
        )
      ]),
      msg="Returns False when one of the BackupFile's in the list has an extension different than .tgz"
    )

  def test_is_corrupted(self):
    self.assertTrue(
      expr=is_corrupted(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0444.tgz',
          size='2'
        ),
        backup_files=[
          BackupFile(
            filename='backup-2020-08-30-0441.tgz',
            size='1'
          ),
          BackupFile(
            filename='backup-2020-08-30-0442.tgz',
            size='2'
          ),
          BackupFile(
            filename='backup-2020-08-30-0443.tgz',
            size='3'
          )
        ]
      ),
      msg=str(
        "Returns False when the backup file passed is newer than a backup file from the list passed yet is smaller "
        "than this backup file from the list"
      )
    )

    self.assertFalse(
      expr=is_corrupted(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0440.tgz',
          size='1'
        ),
        backup_files=[]
      ),
      msg=str(
        'Returns False when the list of backup files passed is empty, the backup file passed has a size greater than '
        'zero and has the .tgz extension'
      )
    )

    self.assertTrue(
      expr=is_corrupted(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0455.tar.gz',
          size='1'
        ),
        backup_files=[]
      ),
      msg=str(
        'Returns True when backup file passed does not have a .tgz extension'
      )
    )

    self.assertTrue(
      expr=is_corrupted(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0456.tgz',
          size='0'
        ),
        backup_files=[]
      ),
      msg=str(
        'Returns True when backup file passed has size zero'
      )
    )

    self.assertFalse(
      expr=is_corrupted(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0448.tgz',
          size='4'
        ),
        backup_files=[
          BackupFile(
            filename='backup-2020-08-30-0445.tgz',
            size='1'
          ),
          BackupFile(
            filename='backup-2020-08-30-0446.tgz',
            size='2'
          ),
          BackupFile(
            filename='backup-2020-08-30-0447.tgz',
            size='3'
          ),
          BackupFile(
            filename='backup-2020-08-30-0453.tgz',
            size='5'
          )
        ]
      ),
      msg=str(
        'Returns False when the backup file passed is only bigger than the older files in the list, has a size greater '
        'than zero and has the .tgz extension'
      )
    )

    self.assertFalse(
      expr=is_corrupted(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0452.tgz',
          size='3'
        ),
        backup_files=[
          BackupFile(
            filename='backup-2020-08-30-0449.tgz',
            size='1'
          ),
          BackupFile(
            filename='backup-2020-08-30-0450.tgz',
            size='2'
          ),
          BackupFile(
            filename='backup-2020-08-30-0451.tgz',
            size='3'
          ),
          BackupFile(
            filename='backup-2020-08-30-0454.tgz',
            size='4'
          )
        ]
      ),
      msg=str(
        'Returns False when the backup file passed is only bigger or equal in size than the older files in the list, '
        'has a size greater than zero and has the .tgz extension'
      )
    )

  def test_is_smaller_than_older(self):
    self.assertFalse(
      expr=is_smaller_than_older(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0452.tgz',
          size='3'
        ),
        backup_files=[]
      ),
      msg='Returns False when the list of backup files is empty'
    )

    self.assertFalse(
      expr=is_smaller_than_older(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0452.tgz',
          size='3'
        ),
        backup_files=[
          BackupFile(
            filename='backup-2020-08-30-0449.tgz',
            size='1'
          ),
          BackupFile(
            filename='backup-2020-08-30-0450.tgz',
            size='2'
          ),
          BackupFile(
            filename='backup-2020-08-30-0451.tgz',
            size='3'
          ),
          BackupFile(
            filename='backup-2020-08-30-0454.tgz',
            size='4'
          )
        ]
      ),
      msg=str(
        'Returns False when the only backup files on the list that are bigger then the backup file passed are the '
        'newer ones'
      )
    )

    self.assertTrue(
      expr=is_smaller_than_older(
        backup_file=BackupFile(
          filename='backup-2020-08-30-0452.tgz',
          size='2'
        ),
        backup_files=[
          BackupFile(
            filename='backup-2020-08-30-0449.tgz',
            size='1'
          ),
          BackupFile(
            filename='backup-2020-08-30-0450.tgz',
            size='2'
          ),
          BackupFile(
            filename='backup-2020-08-30-0451.tgz',
            size='3'
          ),
          BackupFile(
            filename='backup-2020-08-30-0454.tgz',
            size='4'
          )
        ]
      ),
      msg=str(
        'Returns True when there are backup files on the list that are bigger then the backup file passed and are also '
        'older than it is'
      )
    )

  def test_newest_backup(self):
    self.assertIsNone(
      obj=newest_backup(backup_files=[]),
      msg='Returns None when the list of backup files is empty'
    )

    old_backup_file_a = BackupFile(
      filename='backup-2020-09-06-0448.tgz',
      size='1'
    )
    old_backup_file_b = BackupFile(
      filename='backup-2020-09-06-0449.tgz',
      size='1'
    )
    new_backup_file = BackupFile(
      filename='backup-2020-09-06-0450.tgz',
      size='1'
    )
    self.assertEqual(
      first=new_backup_file,
      second=newest_backup(
        backup_files=[old_backup_file_a, new_backup_file, old_backup_file_b]
      ),
      msg='Returns the newest backup file on the list of backup files passed'
    )

  def test_disposable_backups(self):
    self.assertEqual(
      first=[],
      second=disposable_backups(backup_files=[], keeping_quantity=0),
      msg='Returns an empty list when the list of backup files is empty'
    )
    self.assertEqual(
      first=[],
      second=disposable_backups(
        backup_files=[BackupFile(filename='backup-2020-09-06-0440.tgz', size='1')],
        keeping_quantity=1
      ),
      msg=str(
        'Returns an empty list when the list of backup files has less than or exactly the keeping quantity of '
        'backup_files'
      )
    )
    self.assertEqual(
      first=[],
      second=disposable_backups(
        backup_files=[
          BackupFile(filename='backup-2020-09-06-0441.tgz', size='1')
        ],
        keeping_quantity=2
      ),
      msg=str(
        'Returns an empty list when the list of backup files has less than or exactly the keeping quantity of '
        'backup_files'
      )
    )
    self.assertEqual(
      first=[],
      second=disposable_backups(
        backup_files=[
          BackupFile(filename='backup-2020-09-06-0442.tgz', size='1'),
          BackupFile(filename='backup-2020-09-06-0443.tgz', size='1')
        ],
        keeping_quantity=2
      ),
      msg=str(
        'Returns an empty list when the list of backup files has less than or exactly the keeping quantity of '
        'backup_files'
      )
    )

    disposable = [BackupFile(filename='backup-2020-09-06-0444.tgz', size='1')]
    self.assertEqual(
      first=disposable,
      second=disposable_backups(backup_files=disposable, keeping_quantity=0),
      msg='Returns the list of backup files that exceeds the keeping quantity specified'
    )

    old_backup_file_a = BackupFile(
      filename='backup-2020-09-06-0445.tgz',
      size='1'
    )
    old_backup_file_b = BackupFile(
      filename='backup-2020-09-06-0446.tgz',
      size='1'
    )
    new_backup_file = BackupFile(
      filename='backup-2020-09-06-0447.tgz',
      size='1'
    )
    self.assertEqual(
      first=[old_backup_file_a, old_backup_file_b],
      second=disposable_backups(
        backup_files=[old_backup_file_a, new_backup_file, old_backup_file_b],
        keeping_quantity=1
      ),
      msg='Returns the oldest backup files that exceeds the keeping quantity of backups files specified'
    )

  def test_backup_files_found(self):
    self.assertEqual(
      first=[],
      second=backup_files_found(sftp_attributes_from_files=[]),
      msg='Returns an empty list when the list of sftp attributes is empty'
    )

    file_a = SFTPAttributesMock(filename='filename', st_size=1)
    file_b = SFTPAttributesMock(
      filename='backup-2020-09-27-0441.tgz',
      st_size=2
    )

    self.assertEqual(
      first=[BackupFile(filename=file_b.filename, size=file_b.st_size)],
      second=backup_files_found(sftp_attributes_from_files=[file_a, file_b]),
      msg=str(
        'Returns a list with a backup file for each SFTPAttributes object in the list passed that has the filename '
        'starting with backup and with some extension'
      )
    )

  def test_is_valid_backup_filename(self):
    self.assertFalse(
      expr=is_valid_backup_filename(filename='.lastbackup'),
      msg='Returns False for the hidden file .lastbackup that usually is found on the backups directory'
    )

    self.assertTrue(
      expr=is_valid_backup_filename(filename='backup-2020-09-27-0440.tgz'),
      msg='Returns False for the hidden file .lastbackup that usually is found on the backups directory'
    )

  def test_retrieved_file(self):
    current_remotepath = MagicMock()
    current_localpath = MagicMock()
    sftp = MagicMock()

    self.assertEqual(
      first=current_localpath,
      second=retrieved_file(
        current_remotepath=current_remotepath,
        current_localpath=current_localpath,
        sftp=sftp
      ),
      msg='Returns the localpath of the file retrieved'
    )
    self.assertIn(
      member=call.get(
        remotepath=current_remotepath,
        localpath=current_localpath
      ),
      container=sftp.mock_calls,
      msg='Gets the remote file to the localpath using the sftp passed'
    )

  def test_remotepath(self):
    remote_directory = '/some/directory/'
    filename = 'file.ext'
    self.assertEqual(
      first=PurePath('/some/directory/file.ext'),
      second=remotepath(
        remote_directory=remote_directory,
        filename=filename
      )
    )

  def test_labeled_backups(self):
    newest_backup_file = BackupFile(
      filename='backup-2020-09-29-0442.tgz',
      size=3
    )
    ordinary_backup_file = BackupFile(
      filename='backup-2020-09-29-0441.tgz',
      size=2
    )
    disposable_backup_file = BackupFile(
      filename='backup-2020-09-29-0440.tgz',
      size=1
    )

    self.assertEqual(
      first={
        'newest_backup': newest_backup_file,
        'disposable_backups': [disposable_backup_file]
      },
      second=labeled_backups(
        backup_files=[
          ordinary_backup_file,
          newest_backup_file,
          disposable_backup_file
        ],
        keeping_quantity=2
      ),
      msg=str(
        'Returns a dict with the the newest and the disposable backups on the list of backups passed based on the '
        'keeping quantity passed'
      )
    )

  def test_retrieved_and_deleted_backups(self):
    backup_settings = {
      'remote_backups_directory': '/remote/directory/',
      'local_backups_directory': 'C:\\Users\\someone\\'
    }

    current_labeled_backups = {
      'newest_backup': BackupFile(
        filename='backup-2020-09-29-0444.tgz',
        size=5
      ),
      'disposable_backups': [
        BackupFile(filename='backup-2020-09-29-0443.tgz', size=4)
      ]
    }

    self.assertEqual(
      first={
        'retrieved_backup': PurePath('C:\\Users\\someone\\backup-2020-09-29-0444.tgz'),
        'deleted_backups': [PurePath('/remote/directory/backup-2020-09-29-0443.tgz')]
      },
      second=retrieved_and_deleted_backups(
        current_labeled_backups=current_labeled_backups,
        backup_settings=backup_settings,
        sftp=MagicMock())
    )

  def test_deleted_remote_backup_files(self):
    remote_backups_directory = '/admin/backup/'
    backup_files = [BackupFile(filename='backup-2020-10-11-0440.tgz', size=1)]
    sftp = MagicMock()

    self.assertEqual(
      first=[PurePath('/admin/backup/backup-2020-10-11-0440.tgz')],
      second=deleted_remote_backup_files(
        remote_directory=remote_backups_directory,
        backup_files=backup_files,
        sftp=sftp
      ),
      msg='Returns the disposable backup files that were sent to be deleted remotely'
    )
    self.assertIn(
      member=[
        call.unlink(
          path=remotepath(
            remote_directory=remote_backups_directory,
            filename=backup_file.filename
          )
        ) for backup_file in backup_files
      ],
      container=sftp.mock_calls,
      msg='Each one of the backup file passed is unlinked from the the remote backups directory'
    )

  def test_deleted_remote_file(self):
    file_remotepath = PurePath('/admin/backup/backup-2020-10-11-0440.tgz')
    sftp = MagicMock()

    self.assertEqual(
      first=file_remotepath,
      second=deleted_remote_file(
        file_remotepath=file_remotepath,
        sftp=sftp
      )
    )
    self.assertIn(
      member=[call.unlink(path=file_remotepath)],
      container=sftp.mock_calls,
      msg='The backup file passed is unlinked from the the remote backups directory'
    )

  @patch(target='backup.myauth.open_ssh_session')
  @patch(target='backup.myauth.retrieved_and_deleted_backups')
  def test_myauth_backup(
    self,
    mock_retrieved_and_deleted_backups,
    mock_open_ssh_session
  ):
    ssh_client_options = {
      'hosts_keys_filename': 'tests/hosts_keys',
    }
    myauth = {
      'backup_settings': {
        'local_backups_directory': 'C:\\Users\\me\\backups\\',
        'remote_backups_directory': '/admin/backup/',
        'keeping_backups_quantity': 7
      },
      'credentials': {
        'username': 'user',
        'hostname': 'host',
        'port': 1234,
        'pkey': 'key'
      }
    }

    self.assertEqual(
      first=mock_retrieved_and_deleted_backups.return_value,
      second=myauth_backup(
        myauth=myauth,
        ssh_client_options=ssh_client_options
      ),
      msg='Returns the path for the local retrieved and the remotely deleted backup files'
    )

    self.assertIn(
      member=call(
        client_options=ssh_client_options,
        credentials=myauth['credentials']
      ),
      container=mock_open_ssh_session.mock_calls,
      msg='Uses the ssh client options and the credentials from the myauth settings passed to open the ssh session'
    )
