from datetime import datetime, timedelta
from pathlib import PurePath
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from backup.routerboard import make_filename, current_datetime, backup_filename, script_filename, \
  backup_command, \
  export_command, make_delete_file_command, generate_backup, localpath, make_remotepath, retrieve_file, \
  delete_remote_file, clean_remote_backup_files, retrieve_backup_files, generate_export_script, backup, \
  remote_file_exists, timeout, assert_remote_file_exists, remotepath_without_root
import config


class TestBackupFunctions(TestCase):

  def test_current_datetime(self):
    before_execution = datetime.now().replace(microsecond=0)
    actual_current_datetime = current_datetime()
    after_execution = datetime.now().replace(microsecond=0)
    result = datetime.strptime(actual_current_datetime, '%Y-%m-%d-%H-%M-%S')
    self.assertTrue(expr=before_execution <= result <= after_execution)

  @patch(target='backup.routerboard.current_datetime', return_value='some datetime')
  def test_make_filename(self, mock_current_datetime):
    prefix = 'prefix'
    expected_filename = 'prefix_{current_datetime}'.format(current_datetime=mock_current_datetime.return_value)
    self.assertEqual(first=expected_filename, second=make_filename(prefix=prefix))

  @patch(target='backup.routerboard.make_filename', return_value='some filename')
  def test_backup_filename(self, mock_make_filename):
    device_id = 'some id'
    expected_filename = '{filename}.backup'.format(filename=mock_make_filename.return_value)
    self.assertEqual(first=expected_filename, second=backup_filename(device_id=device_id))
    mock_make_filename.assert_called_once_with(prefix=device_id)

  @patch(target='backup.routerboard.make_filename', return_value='some filename')
  def test_script_filename(self, mock_make_filename):
    device_id = 'some id'
    expected_filename = '{filename}.rsc'.format(filename=mock_make_filename.return_value)
    self.assertEqual(first=expected_filename, second=script_filename(device_id=device_id))
    mock_make_filename.assert_called_once_with(prefix=device_id)

  @patch(target='backup.routerboard.backup_filename', return_value='backup filename')
  def test_backup_command(self, mock_make_backup_filename):
    config.backup_password = 'some password'
    device_id = 'some id'

    expected_backup_command = {
      'command': str(
        '/system backup save name={backup_filename} password={backup_password}'
      ).format(backup_filename=mock_make_backup_filename.return_value, backup_password=config.backup_password),
      'filename': mock_make_backup_filename.return_value,
    }

    self.assertEqual(first=expected_backup_command, second=backup_command(device_id=device_id))
    mock_make_backup_filename.assert_called_once_with(device_id=device_id)

  @patch(target='backup.routerboard.script_filename', return_value='script filename')
  def test_export_command(self, mock_make_script_filename):
    device_id = 'some id'
    expected_script_command = {
      'command': '/ export file={script_filename}'.format(script_filename=mock_make_script_filename.return_value),
      'filename': mock_make_script_filename.return_value,
    }
    self.assertEqual(first=expected_script_command, second=export_command(device_id=device_id))
    mock_make_script_filename.assert_called_once_with(device_id=device_id)

  def test_make_delete_file_command(self):
    filename = 'some file'
    expected_delete_file_command = '/file remove {filename}'.format(filename=filename)
    self.assertEqual(first=expected_delete_file_command, second=make_delete_file_command(filename=filename))

  @patch(target='backup.routerboard.backup_command')
  def test_generate_backup(self, mock_make_backup_command):
    mock_make_backup_command.return_value = {'command': 'something', 'filename': 'some_file'}
    device_id = 'some id'
    mock_ssh = MagicMock()
    expected_behaviour = [
      call.exec_command(command=mock_make_backup_command.return_value['command'])
    ]

    self.assertEqual(
      first=mock_make_backup_command.return_value['filename'],
      second=generate_backup(device_id=device_id, ssh=mock_ssh)
    )

    self.assertEqual(first=expected_behaviour, second=mock_ssh.mock_calls)

  @patch(target='backup.routerboard.export_command')
  def test_generate_export_script(self, mock_make_export_command):
    mock_make_export_command.return_value = {'command': 'something', 'filename': 'some_file'}
    device_id = 'some id'
    mock_ssh = MagicMock()
    expected_behaviour = [
      call.exec_command(command=mock_make_export_command.return_value['command'])
    ]

    self.assertEqual(
      first=mock_make_export_command.return_value['filename'],
      second=generate_export_script(device_id=device_id, ssh=mock_ssh)
    )

    self.assertEqual(first=expected_behaviour, second=mock_ssh.mock_calls)

  def test_localpath(self):
    filename = 'file name'
    expected_localpath = PurePath('{backup_files_directory_path}/{filename}'.format(
      backup_files_directory_path=config.backup_files_directory_path,
      filename=filename
    ))
    self.assertEqual(first=expected_localpath, second=localpath(filename=filename))

  def test_make_remotepath(self):
    filename = 'file name'
    expected_localpath = PurePath('/{filename}'.format(filename=filename))
    self.assertEqual(first=expected_localpath, second=make_remotepath(filename=filename))

  @patch(target='backup.routerboard.remotepath_without_root', return_value='some/path')
  @patch(target='backup.routerboard.assert_remote_file_exists')
  @patch(target='backup.routerboard.localpath', return_value='local path')
  @patch(target='backup.routerboard.make_remotepath', return_value='remote path')
  def test_retrieve_file(
    self, mock_make_remote_path, mock_make_local_path, mock_assert_remote_file_exists, mock_remotepath_without_root
  ):
    config.backup_files_directory_path = 'backup files directory path'
    mock_sftp_session = MagicMock()
    filename = 'some filename'

    expected_behaviour = [
      call.get(remotepath=mock_remotepath_without_root.return_value, localpath=mock_make_local_path.return_value)
    ]

    mock_assert_remote_file_exists.return_value = True
    self.assertEqual(
      first=mock_make_local_path.return_value,
      second=retrieve_file(filename, sftp=mock_sftp_session)
    )
    self.assertEqual(first=expected_behaviour, second=mock_sftp_session.mock_calls)
    mock_make_remote_path.assert_called_once_with(filename=filename)

    mock_assert_remote_file_exists.return_value = False
    self.assertFalse(expr=retrieve_file(filename, sftp=mock_sftp_session))

  @patch(target='backup.routerboard.make_remotepath', return_value='remote path')
  def test_delete_remote_file(self, mock_make_remotepath):
    filename = 'some filename'
    mock_sftp_session = MagicMock()
    expected_behaviour = [
      call.unlink(path=mock_make_remotepath.return_value)
    ]
    delete_remote_file(filename=filename, sftp=mock_sftp_session)
    mock_make_remotepath.assert_called_once_with(filename=filename)
    self.assertEqual(first=expected_behaviour, second=mock_sftp_session.mock_calls)

  @patch(target='backup.routerboard.delete_remote_file')
  def test_clean_remote_backup_files(self, mock_delete_remote_file):
    filenames = ['filename_a', 'filename_b']
    sftp_session = 'sftp session'
    expected_behaviour = [call(filename=filename, sftp=sftp_session) for filename in filenames]

    clean_remote_backup_files(filenames=filenames, sftp=sftp_session)

    self.assertEqual(first=expected_behaviour, second=mock_delete_remote_file.mock_calls)

  @patch(target='backup.routerboard.retrieve_file', return_value='filepath')
  def test_retrieve_backup_files(self, mock_retrieve_file):
    filenames = ['filename_a', 'filename_b']
    sftp_session = 'sftp session'
    expected_behaviour = [call(filename=filename, sftp=sftp_session) for filename in filenames]

    self.assertEqual(
      first=[mock_retrieve_file.return_value for i in range(0, len(filenames))],
      second=retrieve_backup_files(filenames=filenames, sftp=sftp_session)
    )

    self.assertEqual(first=expected_behaviour, second=mock_retrieve_file.mock_calls)

  @patch(target='backup.routerboard.retrieve_backup_files', return_value=['first localpath', 'second localpath'])
  @patch(target='backup.routerboard.generate_backup', return_value='backup filename')
  @patch(target='backup.routerboard.generate_export_script', return_value='script filename')
  def test_backup(self, mock_generate_export_script, mock_generate_backup, mock_retrieve_backup_files):
    ssh = MagicMock()
    device_id = 'device id'

    self.assertEqual(first=mock_retrieve_backup_files.return_value, second=backup(device_id=device_id, ssh=ssh))
    mock_generate_backup.assert_called_once_with(device_id=device_id)
    mock_generate_export_script.assert_called_once_with(device_id=device_id)

  @patch(target='backup.routerboard.remotepath_without_root', return_value='something')
  def test_remote_file_exists(self, mock_remotepath_parent):
    sftp = MagicMock()

    remotepath = PurePath('/path/to/file')
    sftp.listdir.return_value = ['']
    self.assertFalse(expr=remote_file_exists(remotepath=remotepath, sftp=sftp))
    sftp.listdir.assert_called_once_with(path=mock_remotepath_parent.return_value)

    sftp.listdir.return_value = ['file']
    self.assertTrue(expr=remote_file_exists(remotepath=remotepath, sftp=sftp))

  @patch('backup.routerboard.datetime')
  def test_timeout(self, mock_datetime):
    start_time = datetime.now()
    mock_datetime.now.return_value = start_time
    seconds = 1
    self.assertFalse(expr=timeout(start_time=start_time, seconds=seconds))

    mock_datetime.now.return_value = start_time + timedelta(seconds=seconds)
    self.assertTrue(expr=timeout(start_time=start_time, seconds=seconds))

  @patch(target='backup.routerboard.remote_file_exists')
  @patch(target='backup.routerboard.timeout')
  def test_assert_remote_file_exists(self, mock_timeout, mock_remote_file_exists):
    mock_timeout.return_value = True
    mock_remote_file_exists.return_value = False
    self.assertFalse(expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''))

    mock_timeout.return_value = True
    mock_remote_file_exists.return_value = True
    self.assertTrue(expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''))

    mock_timeout.return_value = False
    mock_remote_file_exists.return_value = True
    self.assertTrue(expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''))

    mock_timeout.return_value = False
    mock_remote_file_exists.side_effect = [False, True, True]
    self.assertTrue(expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''))

  def test_remotepath_without_root(self):
    self.assertEqual(first='.', second=remotepath_without_root(remotepath=PurePath('/')))
    self.assertEqual(first='file', second=remotepath_without_root(remotepath=PurePath('/file')))
    remote_path = PurePath('/something/file')
    self.assertEqual(first='something/file', second=remotepath_without_root(remotepath=remote_path))
