from paramiko import RSAKey

server_private_key = RSAKey(filename=r'C:\Users\sergio\backup_manager\tests\server_private_key')
client_private_key = RSAKey(filename=r'C:\Users\sergio\backup_manager\tests\client_private_key')

username = 'my_username'
port = 2222

ssh_client_options = {
  'hosts_keys_filename': r'C:\Users\sergio\backup_manager\tests\hosts_keys',
}

ssh_credentials = {
  'username': username,
  'hostname': 'localhost',
  'port': port,
  'pkey': client_private_key,
}

backup_password = 'not that secret'
