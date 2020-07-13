from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from backup_manager.routerboard_backup import make_filename, current_datetime, make_backup_filename, make_script_filename, \
  make_backup_command, \
  make_export_command, make_delete_file_command, generate_backup, make_localpath, make_remotepath, retrieve_file, \
  delete_remote_file, clean_remote_backup_files, retrieve_backup_files
import config


class TestBackupFunctions(TestCase):

  def test_current_datetime(self):
    before_execution = datetime.now().replace(microsecond=0)
    actual_current_datetime = current_datetime()
    after_execution = datetime.now().replace(microsecond=0)
    result = datetime.strptime(actual_current_datetime, '%Y-%m-%d-%H-%M-%S')
    self.assertTrue(expr=before_execution <= result <= after_execution)

  @patch(target='backup_manager.routerboard_backup.current_datetime', return_value='some datetime')
  def test_make_filename(self, mock_current_datetime):
    prefix = 'prefix'
    expected_filename = 'prefix_{current_datetime}'.format(current_datetime=mock_current_datetime.return_value)
    self.assertEqual(first=expected_filename, second=make_filename(prefix=prefix))

  @patch(target='backup_manager.routerboard_backup.make_filename', return_value='some filename')
  def test_make_backup_filename(self, mock_make_filename):
    device_id = 'some id'
    expected_filename = '{filename}.backup'.format(filename=mock_make_filename.return_value)
    self.assertEqual(first=expected_filename, second=make_backup_filename(device_id=device_id))
    mock_make_filename.assert_called_once_with(prefix=device_id)

  @patch(target='backup_manager.routerboard_backup.make_filename', return_value='some filename')
  def test_make_script_filename(self, mock_make_filename):
    device_id = 'some id'
    expected_filename = '{filename}.rsc'.format(filename=mock_make_filename.return_value)
    self.assertEqual(first=expected_filename, second=make_script_filename(device_id=device_id))
    mock_make_filename.assert_called_once_with(prefix=device_id)

  @patch(target='backup_manager.routerboard_backup.make_backup_filename', return_value='backup filename')
  def test_make_backup_command(self, mock_make_backup_filename):
    config.backup_password = 'some password'
    device_id = 'some id'

    expected_backup_command = {
      'command': str(
        '/system backup save name={backup_filename} password={backup_password}'
      ).format(backup_filename=mock_make_backup_filename.return_value, backup_password=config.backup_password),
      'filename': mock_make_backup_filename.return_value,
    }

    self.assertEqual(first=expected_backup_command, second=make_backup_command(device_id=device_id))
    mock_make_backup_filename.assert_called_once_with(device_id=device_id)

  @patch(target='backup_manager.routerboard_backup.make_script_filename', return_value='script filename')
  def test_make_export_command(self, mock_make_script_filename):
    device_id = 'some id'
    expected_script_command = {
      'command': '/ export file={script_filename}'.format(script_filename=mock_make_script_filename.return_value),
      'filename': mock_make_script_filename.return_value,
    }
    self.assertEqual(first=expected_script_command, second=make_export_command(device_id=device_id))
    mock_make_script_filename.assert_called_once_with(device_id=device_id)

  def test_make_delete_file_command(self):
    filename = 'some file'
    expected_delete_file_command = '/file remove {filename}'.format(filename=filename)
    self.assertEqual(first=expected_delete_file_command, second=make_delete_file_command(filename=filename))

  @patch(target='backup_manager.routerboard_backup.make_backup_command')
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

  def test_make_localpath(self):
    filename = 'file name'
    expected_localpath = '{backup_files_directory_path}/{filename}'.format(
      backup_files_directory_path=config.backup_files_directory_path,
      filename=filename
    )
    self.assertEqual(first=expected_localpath, second=make_localpath(filename=filename))

  def test_make_remotepath(self):
    filename = 'file name'
    expected_localpath = '/{filename}'.format(filename=filename)
    self.assertEqual(first=expected_localpath, second=make_remotepath(filename=filename))

  @patch(target='backup_manager.routerboard_backup.make_localpath', return_value='local path')
  @patch(target='backup_manager.routerboard_backup.make_remotepath', return_value='remote path')
  def test_retrieve_file(self, mock_make_remote_path, mock_make_local_path):
    config.backup_files_directory_path = 'backup files directory path'
    mock_sftp_session = MagicMock()
    filename = 'some filename'

    expected_behaviour = [
      call.get(remotepath=mock_make_remote_path.return_value, localpath=mock_make_local_path.return_value)
    ]

    self.assertEqual(
      first=mock_make_local_path.return_value,
      second=retrieve_file(filename, sftp=mock_sftp_session)
    )

    self.assertEqual(first=expected_behaviour, second=mock_sftp_session.mock_calls)

  @patch(target='backup_manager.routerboard_backup.make_remotepath', return_value='remote path')
  def test_delete_remote_file(self, mock_make_remotepath):
    filename = 'some filename'
    mock_sftp_session = MagicMock()
    expected_behaviour = [
      call.unlink(path=mock_make_remotepath.return_value)
    ]
    delete_remote_file(filename=filename, sftp=mock_sftp_session)
    mock_make_remotepath.assert_called_once_with(filename=filename)
    self.assertEqual(first=expected_behaviour, second=mock_sftp_session.mock_calls)

  @patch(target='backup_manager.routerboard_backup.delete_remote_file')
  def test_clean_remote_backup_files(self, mock_delete_remote_file):
    filenames = ['filename_a', 'filename_b']
    sftp_session = 'sftp session'
    expected_behaviour = [call(filename=filename, sftp=sftp_session) for filename in filenames]

    clean_remote_backup_files(filenames=filenames, sftp=sftp_session)

    self.assertEqual(first=expected_behaviour, second=mock_delete_remote_file.mock_calls)

  @patch(target='backup_manager.routerboard_backup.retrieve_file', return_value='filepath')
  def test_retrieve_backup_files(self, mock_retrieve_file):
    filenames = ['filename_a', 'filename_b']
    sftp_session = 'sftp session'
    expected_behaviour = [call(filename=filename, sftp=sftp_session) for filename in filenames]

    self.assertEqual(
      first=[mock_retrieve_file.return_value for i in range(0, len(filenames))],
      second=retrieve_backup_files(filenames=filenames, sftp=sftp_session)
    )

    self.assertEqual(first=expected_behaviour, second=mock_retrieve_file.mock_calls)
