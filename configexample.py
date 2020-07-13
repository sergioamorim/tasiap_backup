# The actual config file needs to be named config.py
from paramiko import RSAKey

ssh_client_options = {
  'hosts_keys_filename': '/path/to/known_hosts',
}

# credentials to the routerboards (currently the same credentials must apply to all routerboards)
ssh_credentials = {
  'username': 'some_username',
  'hostname': 'some_hostname_or_ip',
  'port': 65535,
  'pkey': RSAKey(filename='/path/to/private_key'),
}

backup_password = 'pass'  # password to encrypt the routerboard .backup file

backup_files_directory_path = '/path/to/save/the/backup/files/with/trailing/slash/'  # ensure write permission here
