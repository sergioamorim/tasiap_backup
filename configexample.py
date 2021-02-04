from paramiko import RSAKey

ssh_client_options = {
  'hosts_keys_filename': '/path/to/known_hosts',
}

routerboards = [
  {
    'name': 'router-identification',
    'backup_options': {
      'backups_directory': '/path/to/save/the/backup/files/with/trailing/slash/',
      'assertion_options': {
        'seconds_to_timeout': 10,
        'minimum_size_in_bytes': 77
      }
    },
    'backup_password': 'pass',  # used to encrypt the .backup file
    'credentials': {
      'username': 'some_username',
      'hostname': 'some_hostname_or_ip',
      'port': 65535,
      'pkey': RSAKey(filename='/path/to/private_key')
    }
  }
]

myauth = {
  'backup_settings': {
    'local_backups_directory': '/path/to/save/the/backup/files/with/trailing/slash/',
    'remote_backups_directory': '/admin/backup/',
    'keeping_backups_quantity': 7  # backups older then this number of days will be deleted from the server
  },
  'credentials': {
    'username': 'some_username',
    'hostname': 'some_hostname_or_ip',
    'port': 65535,
    'pkey': RSAKey(filename='/path/to/private_key')
  }
}
