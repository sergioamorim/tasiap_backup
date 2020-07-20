from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from paramiko import SSHClient

import config
from backup.ssh_client import open_ssh_client, close_connection, setup_client, supply_ssh_connection
from tests.ssh_testing_environment import SSHTestingEnvironment
from tests.testing_config import ssh_credentials, ssh_client_options


class TestSSHClientFunctions(TestCase):
  ssh_testing_server = None

  @classmethod
  def setUpClass(cls):
    cls.ssh_testing_server = SSHTestingEnvironment()

  @classmethod
  def tearDownClass(cls):
    cls.ssh_testing_server.stop()

  def test_open_ssh_client(self):
    with open_ssh_client(ssh_client_options=ssh_client_options, ssh_credentials=ssh_credentials) as ssh:
      self.assertTrue(expr=ssh)
      self.assertEqual(first=SSHClient, second=type(ssh))
      self.assertTrue(expr=ssh.get_transport())
      ssh.exec_command(command='exit')
      ssh.exec_command(command='exit')

    with open_ssh_client(ssh_client_options=ssh_client_options, ssh_credentials=ssh_credentials) as ssh:
      ssh.exec_command(command='exit')
    self.assertFalse(expr=ssh.get_transport())


class TestFunctions(TestCase):

  def test_close_connection(self):
    mock_ssh = MagicMock()

    expected_behavior = [
      call.exec_command(command='quit'),
      call.close()
    ]

    close_connection(ssh=mock_ssh)
    self.assertEqual(first=expected_behavior, second=mock_ssh.mock_calls)

  @patch(target='backup.ssh_client.SSHClient')
  def test_setup_client(self, MockSSHClient):

    expected_behavior = [
      call(),
      call().load_host_keys(filename=ssh_client_options['hosts_keys_filename'])
    ]

    setup_client(ssh_client_options=ssh_client_options)
    self.assertEqual(first=expected_behavior, second=MockSSHClient.mock_calls)

  @patch(target='backup.ssh_client.open_ssh_client')
  def test_supply_ssh_connection(self, mock_open_ssh_connection):
    mock_open_ssh_connection.return_value.__enter__.return_value = 'one ssh connection'
    config.ssh_client_options = 'client options'
    config.ssh_credentials = 'ssh credentials'
    other_ssh_connection = 'some other ssh connection'

    @supply_ssh_connection
    def generic_function(ssh=None):
      return ssh

    self.assertEqual(first=mock_open_ssh_connection.return_value.__enter__.return_value, second=generic_function())
    self.assertEqual(first=other_ssh_connection, second=generic_function(ssh=other_ssh_connection))
    mock_open_ssh_connection.assert_called_once_with(
      ssh_client_options=config.ssh_client_options,
      ssh_credentials=config.ssh_credentials
    )
