from paramiko import RSAKey

backups_directory = '/path/to/save/the/backup/files/with/trailing/slash/'

ssh_client_options = {
  'hosts_keys_filename': '/path/to/known_hosts',
}

routerboards = [
  {
    'name': 'router-identification',
    'backup_password': 'pass',  # used to encrypt the .backup file
    'credentials': {
      'username': 'some_username',
      'hostname': 'some_hostname_or_ip',
      'port': 65535,
      'pkey': RSAKey(filename='/path/to/private_key')
    }
  }
]
