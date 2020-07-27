from datetime import datetime, timedelta
from pathlib import PurePath
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import config
from backup.routerboard import make_filename, current_datetime, backup_filename, script_filename, backup_command, \
  export_command, generate_backup, localpath, retrieve_file, retrieve_backup_files, generate_export_script, backup, \
  remote_file_exists, timeout, assert_remote_file_exists, generate_remotely, RemotePath, remotepath_without_root


class TestRemotePath(TestCase):

  def test_init(self):
    path = '/some/path'
    self.assertEqual(
      first=PurePath(path),
      second=RemotePath(path=path).pure,
      msg='Sets the pure property to a PurePath of the path passed'
    )

  @patch(target='backup.routerboard.remotepath_without_root')
  def test_without_root(self, mock_remotepath_without_root):
    remotepath = RemotePath(path='/some/path')
    self.assertEqual(
      first=mock_remotepath_without_root.return_value,
      second=remotepath.without_root,
      msg='Returns the remote path without root'
    )
    self.assertIn(
      member=call(remotepath=remotepath.pure),
      container=mock_remotepath_without_root.mock_calls,
      msg=str(
        'Gather the remote path without root from its pure path'
      )
    )

  @patch(target='backup.routerboard.remotepath_without_root')
  def test_parent_without_root(self, mock_remotepath_without_root):
    remotepath = RemotePath(path='/some/path')
    self.assertEqual(
      first=mock_remotepath_without_root.return_value,
      second=remotepath.parent_without_root,
      msg='Returns the remote path parent without root'
    )
    self.assertIn(
      member=call(remotepath=remotepath.pure.parent),
      container=mock_remotepath_without_root.mock_calls,
      msg=str(
        'Gather the remote path without root from its pure.parent path'
      )
    )


class TestBackupFunctions(TestCase):

  def test_current_datetime(self):
    before_execution = datetime.now().replace(microsecond=0)
    actual_current_datetime = current_datetime()
    after_execution = datetime.now().replace(microsecond=0)
    result = datetime.strptime(actual_current_datetime, '%Y-%m-%d-%H-%M-%S')

    self.assertTrue(
      expr=before_execution <= result <= after_execution,
      msg='Current date and time is between the date and time before and after the execution'
    )

  @patch(target='backup.routerboard.current_datetime', return_value='some datetime')
  def test_make_filename(self, mock_current_datetime):
    prefix = 'prefix'
    expected_filename = '{prefix}_{current_datetime}'.format(
      prefix=prefix,
      current_datetime=mock_current_datetime.return_value
    )

    self.assertEqual(
      first=expected_filename,
      second=make_filename(prefix=prefix),
      msg='The filename returned has the prefix passed and the current date and time split by underscore'
    )

  @patch(target='backup.routerboard.make_filename', return_value='some filename')
  def test_backup_filename(self, mock_make_filename):
    device_id = 'some id'
    expected_filename = '{filename}.backup'.format(filename=mock_make_filename.return_value)
    self.assertEqual(
      first=expected_filename,
      second=backup_filename(device_id=device_id),
      msg='The backup filename has the filename made by make_filename and the extension .backup'
    )
    self.assertEqual(
      first=[call(prefix=device_id)],
      second=mock_make_filename.mock_calls,
      msg='The make_filename function is called once with the device_id passed as prefix parameter'
    )

  @patch(target='backup.routerboard.make_filename', return_value='some filename')
  def test_script_filename(self, mock_make_filename):
    device_id = 'some id'
    expected_filename = '{filename}.rsc'.format(filename=mock_make_filename.return_value)
    self.assertEqual(
      first=expected_filename,
      second=script_filename(device_id=device_id),
      msg='The script filename has the filename made by make_filename and the extension .rsc'
    )
    self.assertEqual(
      first=[call(prefix=device_id)],
      second=mock_make_filename.mock_calls,
      msg='The make_filename function is called once with the device_id passed as prefix parameter'
    )

  @patch(target='backup.routerboard.backup_filename', return_value='backup filename')
  def test_backup_command(self, mock_backup_filename):
    config.backup_password = 'some password'
    device_id = 'some id'

    expected_backup_command = {
      'command': str(
        '/system backup save name={backup_filename} password={backup_password}'
      ).format(backup_filename=mock_backup_filename.return_value, backup_password=config.backup_password),
      'filename': mock_backup_filename.return_value,
    }

    self.assertEqual(
      first=expected_backup_command,
      second=backup_command(device_id=device_id),
      msg=str(
        'A dict with the command and the filename is returned. The filename is acquired by the function '
        'backup_filename. The command has the filename as the name parameter and the backup_password from config as '
        'password parameter'
      )
    )
    self.assertEqual(
      first=[call(device_id=device_id)],
      second=mock_backup_filename.mock_calls,
      msg='The function backup_filename is called only once with the device_id passed'
    )

  @patch(target='backup.routerboard.script_filename', return_value='script filename')
  def test_export_command(self, mock_script_filename):
    device_id = 'some id'
    expected_script_command = {
      'command': '/ export file={script_filename}'.format(script_filename=mock_script_filename.return_value),
      'filename': mock_script_filename.return_value,
    }
    self.assertEqual(
      first=expected_script_command,
      second=export_command(device_id=device_id),
      msg='The export command has the script_filename acquired from the script_filename function as the file parameter'
    )
    self.assertEqual(
      first=[call(device_id=device_id)],
      second=mock_script_filename.mock_calls,
      msg='The function script_filename is called only once with the device_id passed'
    )

  @patch(target='backup.routerboard.backup_command')
  def test_generate_backup(self, mock_backup_command):
    mock_backup_command.return_value = {'command': 'something', 'filename': 'some_file'}
    device_id = 'some id'
    mock_ssh = MagicMock()
    expected_behaviour = [
      call.exec_command(command=mock_backup_command.return_value['command'])
    ]

    self.assertEqual(
      first=mock_backup_command.return_value['filename'],
      second=generate_backup(device_id=device_id, ssh=mock_ssh),
      msg='Returns the filename of the backup file generated'
    )

    self.assertEqual(
      first=expected_behaviour,
      second=mock_ssh.mock_calls,
      msg='Calls the exec_command on the ssh passed with the command acquired from the backup_command function'
    )

  def test_generate_remotely(self):
    def command_maker(device_id):
      return {
        'command': 'some command with {device_id} in it'.format(device_id=device_id),
        'filename': 'some filename with {device_id} in it'.format(device_id=device_id),
      }
    current_device_id = 'my little device'
    ssh = MagicMock()
    self.assertEqual(
      first=command_maker(device_id=current_device_id)['filename'],
      second=generate_remotely(device_id=current_device_id, command_maker=command_maker, ssh=ssh),
      msg='Returns the "filename" value from the dictionary acquired from the command_maker'
    )
    self.assertEqual(
      first=[call.exec_command(command=command_maker(device_id=current_device_id)['command'])],
      second=ssh.mock_calls,
      msg='Executes the command acquired from command_maker on the ssh session passed'
    )

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
      second=generate_export_script(device_id=device_id, ssh=mock_ssh),
      msg='Returns the filename of the script file generated'
    )

    self.assertEqual(
      first=expected_behaviour,
      second=mock_ssh.mock_calls,
      msg='Calls the exec_command on the ssh passed with the command acquired from the backup_command function'
    )

  def test_localpath(self):
    filename = 'file name'
    expected_localpath = PurePath('{backup_files_directory_path}/{filename}'.format(
      backup_files_directory_path=config.backup_files_directory_path,
      filename=filename
    ))
    self.assertEqual(
      first=expected_localpath,
      second=localpath(filename=filename),
      msg='Returns a PurePath with the filename passed on the directory from backup_files_directory_path on config'
    )

  @patch(target='backup.routerboard.assert_remote_file_exists')
  @patch(target='backup.routerboard.localpath', return_value='local path')
  @patch(target='backup.routerboard.RemotePath')
  def test_retrieve_file(self, mock_remotepath, mock_localpath, mock_assert_remote_file_exists):
    config.backup_files_directory_path = 'backup files directory path'
    mock_sftp_session = MagicMock()
    filename = 'some filename'

    mock_assert_remote_file_exists.return_value = True
    self.assertEqual(
      first=mock_localpath.return_value,
      second=retrieve_file(filename=filename, sftp=mock_sftp_session),
      msg='When the remote file exists, returns the localpath of the file retrieved (acquired with localpath function)'
    )
    self.assertEqual(
      first=[
        call.get(remotepath=mock_remotepath().without_root, localpath=mock_localpath.return_value),
        call.unlink(path=mock_remotepath().without_root)
      ],
      second=mock_sftp_session.mock_calls,
      msg=str(
        'Calls .get method on the sftp passed with the remote path without root and localpath acquired from the '
        'localpath function and the .unlink method is called with the remote path without root as the path parameter,'
        'in that order'
      )
    )

    self.assertEqual(
      first=[call(path=filename), call(), call()],
      second=mock_remotepath.mock_calls,
      msg='A RemotePath is created with the filename passed as path parameter'
    )

    mock_assert_remote_file_exists.return_value = False
    self.assertIsNone(
      obj=retrieve_file(filename, sftp=mock_sftp_session),
      msg='When remote file does not exists, return None'
    )

  @patch(target='backup.routerboard.retrieve_file', return_value='filepath')
  def test_retrieve_backup_files(self, mock_retrieve_file):
    filenames = ['filename_a', 'filename_b']
    sftp_session = 'sftp session'
    expected_behaviour = [call(filename=filename, sftp=sftp_session) for filename in filenames]

    self.assertEqual(
      first=[mock_retrieve_file.return_value for _ in range(0, len(filenames))],
      second=retrieve_backup_files(filenames=filenames, sftp=sftp_session),
      msg='Returns the filepaths acquired on the retrieve_file function with each filename passed'
    )

    self.assertEqual(
      first=expected_behaviour,
      second=mock_retrieve_file.mock_calls,
      msg='Calls the retrieve_file function with each filename passed as well as with the sftp passed'
    )

  @patch(target='backup.routerboard.retrieve_backup_files', return_value=['first localpath', 'second localpath'])
  @patch(target='backup.routerboard.generate_backup', return_value='backup filename')
  @patch(target='backup.routerboard.generate_export_script', return_value='script filename')
  def test_backup(self, mock_generate_export_script, mock_generate_backup, mock_retrieve_backup_files):
    ssh = MagicMock()
    device_id = 'device id'

    self.assertEqual(
      first=mock_retrieve_backup_files.return_value,
      second=backup(device_id=device_id, ssh=ssh),
      msg='Returns the list of files that were retrieved (acquired from the function retrieve_backup_files)'
    )
    self.assertEqual(
      first=[call(device_id=device_id, ssh=ssh)],
      second=mock_generate_backup.mock_calls,
      msg='The generate_backup function is called with the device_id passed'
    )
    self.assertEqual(
      first=[call(device_id=device_id, ssh=ssh)],
      second=mock_generate_export_script.mock_calls,
      msg='The generate_export_script function is called with the device_id passed'
    )

  def test_remote_file_exists(self):
    sftp = MagicMock()

    filename = 'file'
    remotepath = RemotePath(path='/path/to/{filename}'.format(filename=filename))
    sftp.listdir.return_value = ['']
    self.assertFalse(
      expr=remote_file_exists(remotepath=remotepath, sftp=sftp),
      msg='Returns False when a list with an empty string is returned from the .listdir method on the sftp passed'
    )
    self.assertEqual(
      first=[call(path=remotepath.parent_without_root)],
      second=sftp.listdir.mock_calls,
      msg='The method .listdir from the sftp passed is called with remote path parent without root as path parameter'
    )

    sftp.listdir.return_value = [filename]
    self.assertTrue(
      expr=remote_file_exists(remotepath=remotepath, sftp=sftp),
      msg='Returns True when the list returned from the .listdir method on the sftp passed contains the filename'
    )

  @patch('backup.routerboard.datetime')
  def test_timeout(self, mock_datetime):
    start_time = datetime.now()
    mock_datetime.now.return_value = start_time
    seconds = 1
    self.assertFalse(
      expr=timeout(start_time=start_time, seconds=seconds),
      msg='Returns False if the amount of seconds has not passed starting from the start_time passed'
    )

    mock_datetime.now.return_value = start_time + timedelta(seconds=seconds)
    self.assertTrue(
      expr=timeout(start_time=start_time, seconds=seconds),
      msg='Returns True if the amount of seconds has passed starting from the start_time passed'
    )

  @patch(target='backup.routerboard.remote_file_exists')
  @patch(target='backup.routerboard.timeout')
  def test_assert_remote_file_exists(self, mock_timeout, mock_remote_file_exists):
    mock_timeout.return_value = True
    mock_remote_file_exists.return_value = False
    self.assertFalse(
      expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''),
      msg='Returns False when the timeout has passed and the file does not exists'
    )

    mock_timeout.return_value = True
    mock_remote_file_exists.return_value = True
    self.assertTrue(
      expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''),
      msg='Returns True if the file exists, regardless of the timeout being expired'
    )

    mock_timeout.return_value = False
    mock_remote_file_exists.return_value = True
    self.assertTrue(
      expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''),
      msg='Returns True if the file exists and the timeout has not expired'
    )

    mock_timeout.return_value = False
    mock_remote_file_exists.side_effect = [False, True, True]
    self.assertTrue(
      expr=assert_remote_file_exists(remotepath='', sftp='', seconds=''),
      msg=str(
        'Returns True even if the file was not there the first time that the check was made,'
        'just the timeout needs to not be expired'
      )
    )

  def test_remotepath_without_root(self):
    self.assertEqual(
      first='.',
      second=remotepath_without_root(remotepath=PurePath('/')),
      msg='Returns relative current directory (.) when the remotepath passed is root'
    )
    self.assertEqual(
      first='file',
      second=remotepath_without_root(remotepath=PurePath('/file')),
      msg=str(
        'Returns only the file or directory name when the remotepath passed if from a file or directory sitting in the '
        'root directory'
      )
    )
    remote_path = PurePath('/something/file')
    self.assertEqual(
      first='something/file',
      second=remotepath_without_root(remotepath=remote_path),
      msg=str(
        'Returns the file or directory path without the root slash when the remotepath is from a file or directory '
        'inside a directory other than root'
      )
    )
