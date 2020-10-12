from pathlib import PurePath
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from backup.ssh_client import open_ssh_session, close_ssh_session, setup_client, active_ssh_session, localpath


class TestFunctions(TestCase):

  @patch(target='backup.ssh_client.close_ssh_session')
  @patch(target='backup.ssh_client.setup_client')
  @patch(target='backup.ssh_client.active_ssh_session')
  def test_open_ssh_session(self, mock_active_ssh_session, mock_setup_client, mock_close_connection):
    client_options = 'options'
    credentials = 'username, password and stuff'
    with open_ssh_session(client_options=client_options, credentials=credentials) as ssh:
      self.assertEqual(
        first=mock_active_ssh_session.return_value,
        second=ssh,
        msg='Returns an active ssh session'
      )
      self.assertIn(
        member=call(
          ssh=mock_setup_client.return_value,
          credentials=credentials
        ),
        container=mock_active_ssh_session.mock_calls,
        msg='Calls for an active session using the ssh object and the credentials passed'
      )
      self.assertIn(
        member=call(client_options=client_options),
        container=mock_setup_client.mock_calls,
        msg='Setup the ssh client with the options passed'
      )
      self.assertListEqual(
        list1=[],
        list2=mock_close_connection.mock_calls,
        msg='Does not close the session while the context is open'
      )
    self.assertEqual(
      first=[call(ssh=ssh)],
      second=mock_close_connection.mock_calls,
      msg='Closes the ssh session after the context is closed'
    )

  def test_active_ssh_session(self):
    ssh = MagicMock()
    credentials = {
      'username': 'user',
      'hostname': 'host',
      'port': 1234,
      'pkey': 'key',
    }

    self.assertEqual(
      first=ssh,
      second=active_ssh_session(ssh=ssh, credentials=credentials),
      msg='Returns the ssh object passed'
    )
    self.assertIn(
      member=call.connect(
        username=credentials['username'],
        hostname=credentials['hostname'],
        port=credentials['port'],
        pkey=credentials['pkey']
      ),
      container=ssh.mock_calls,
      msg='Connects the ssh object using the ssh credentials passed'
    )

  def test_close_connection(self):
    mock_ssh = MagicMock()

    close_ssh_session(ssh=mock_ssh)
    self.assertEqual(
      first=[
        call.exec_command(command='quit'),
        call.close()
      ],
      second=mock_ssh.mock_calls,
      msg='Calls the command "quit" in the SSH session and closes the session'
    )

  @patch(target='backup.ssh_client.SSHClient')
  def test_setup_client(self, MockSSHClient):
    client_options = {
      'hosts_keys_filename': 'tests/hosts_keys',
    }

    setup_client(client_options=client_options)
    self.assertEqual(
      first=[
        call(),
        call().load_host_keys(filename=client_options['hosts_keys_filename'])
      ],
      second=MockSSHClient.mock_calls,
      msg='Loads the host keys from the client_options passed'
    )

  def test_localpath(self):
    filename = 'file name'
    backups_directory = '/some/directory/'
    self.assertEqual(
      first=PurePath('{backups_directory}/{filename}'.format(
        backups_directory=backups_directory,
        filename=filename
      )),
      second=localpath(filename=filename, backups_directory=backups_directory),
      msg='Returns a PurePath with the filename passed on the directory from backups_directory passed'
    )
