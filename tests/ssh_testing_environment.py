from binascii import hexlify
from contextlib import contextmanager
from logging import getLogger, Formatter, FileHandler, StreamHandler, DEBUG
from pathlib import Path
from socket import socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, AF_INET6
from threading import Event, Thread
from time import sleep

from paramiko import AUTH_SUCCESSFUL, AUTH_FAILED, Transport, OPEN_SUCCEEDED, OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED, \
  SSHClient, AutoAddPolicy
from paramiko.server import ServerInterface

from tests import testing_config

LOG_LEVEL = DEBUG
LOGS_PATH = r'C:\Users\sergio\backup_manager\logs\\'


class SSHTestingEnvironment:
  def __init__(self):
    self.socket_thread = SocketThread()
    self.socket_thread.start()
    while not self.socket_thread.socket_open:
      sleep(.001)
    self.environment_thread = SSHTestingEnvironmentThread(socket_open=self.socket_thread.socket_open)
    self.environment_thread.start()

  def stop(self):
    self.environment_thread.stop()
    self.socket_thread.stop()
    if self.environment_thread.listening:
      ssh_client = SSHClient()
      ssh_client.set_missing_host_key_policy(AutoAddPolicy)
      ssh_client.connect(
        username=testing_config.username,
        hostname='localhost',
        port=testing_config.port,
        pkey=testing_config.client_private_key
      )
      ssh_client.close()


def kind_not_supported(kind):
  log_kind_not_supported(kind=kind)
  return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


def log_kind_not_supported(kind):
  error_msg = 'A session could not be granted for the given kind: {kind}'
  log.error(msg=error_msg.format(kind=kind))


def auth_failed(key, username):
  log_auth_failed(key=key, username=username)
  return AUTH_FAILED


def log_auth_failed(key, username):
  message = auth_failed_message(key=key, username=username)
  log.error(msg=message)


def auth_failed_message(key, username):
  error_msg = 'Authentication failed with the given username ({username}) and public key ({public_key}).'
  public_key = key_fingerprint(key=key)
  return error_msg.format(username=username, public_key=public_key)


def key_fingerprint(key):
  return hexlify(key.get_fingerprint()).decode('ascii')


def credentials_are_valid(key, username):
  return username == testing_config.username and key == testing_config.client_private_key


def kind_supported(kind):
  return kind == 'session'


class SSHTestingEnvironmentInterface(ServerInterface):

  def __init__(self):
    self.event = Event()

  def check_auth_publickey(self, username, key):
    if credentials_are_valid(key=key, username=username):
        return AUTH_SUCCESSFUL
    return auth_failed(key=key, username=username)

  def get_allowed_auths(self, username):
    return 'public_key'

  def check_channel_request(self, kind, chanid):
    if kind_supported(kind=kind):
      return OPEN_SUCCEEDED
    return kind_not_supported(kind=kind)

  def check_channel_exec_request(self, channel, command):
    return True


class InterruptableThread(Thread):
  interrupt = False

  def wait_for_interruption(self):
    while not self.interrupt:
      sleep(.001)

  def stop(self):
    self.interrupt = True


class SSHTestingEnvironmentThread(InterruptableThread):
  listening = False

  def __init__(self, socket_open):
    super().__init__()
    self.socket_open = socket_open

  def run(self):
    server_interface = SSHTestingEnvironmentInterface()
    while not self.interrupt:
      with create_connection_thread(socket_open=self.socket_open) as connection_thread:
        self.listening = True
        with open_server_transport(server_interface=server_interface, socket_bound=connection_thread.socket_bound
                                   ) as server_transport:
          self.listening = False
          if channel := server_transport.accept():
            while not channel.closed:
              server_interface.event.wait(.001)


class ConnectionThread(InterruptableThread):
  socket_bound = None

  def __init__(self, socket_open):
    super().__init__()
    self.socket_open = socket_open

  def run(self):
    with bound_socket(self.socket_open) as socket_bound:
      self.socket_bound = socket_bound
      self.wait_for_interruption()


class SocketThread(InterruptableThread):
  socket_open = None

  def run(self):
    with open_socket() as socket_open:
      self.socket_open = socket_open
      self.wait_for_interruption()


@contextmanager
def create_connection_thread(socket_open):
  connection_thread = ConnectionThread(socket_open=socket_open)
  connection_thread.start()
  while not connection_thread.socket_bound:
    sleep(.001)
  try:
    yield connection_thread
  finally:
    connection_thread.stop()


@contextmanager
def bound_socket(socket_open):
  socket_open.listen()
  socket_bound, address = socket_open.accept()
  try:
    yield socket_bound
  finally:
    socket_bound.close()


@contextmanager
def open_server_transport(server_interface, socket_bound):
    server_transport = Transport(sock=socket_bound)
    server_transport.add_server_key(key=testing_config.server_private_key)
    server_transport.start_server(server=server_interface)
    try:
      yield server_transport
    finally:
      server_transport.close()


@contextmanager
def open_socket():
  socket_open = socket(family=AF_INET6, type=SOCK_STREAM)
  socket_open.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
  socket_open.bind(('localhost', testing_config.port))
  try:
    yield socket_open
  finally:
    socket_open.close()


def get_logger(name):
  file_path = Path(LOGS_PATH + name + '.log')
  Path(LOGS_PATH).mkdir(parents=True, exist_ok=True)
  logger = getLogger(name)
  logger.setLevel(LOG_LEVEL)
  formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  file_handler = FileHandler(file_path, encoding='utf-8')
  file_handler.setFormatter(formatter)
  stream_handler = StreamHandler()
  stream_handler.setFormatter(formatter)
  logger.addHandler(file_handler)
  logger.addHandler(stream_handler)
  return logger


log = getLogger(__name__)


def file_that_exists(filepath):
  file = Path(filepath)
  if file.is_file():
    return file

  log.error(msg='File not found: {filepath}'.format(filepath=filepath))
  return None
