## tasiap_backup
[![Build Status](https://travis-ci.org/sergioamorim/tasiap_backup.svg?branch=master)](https://travis-ci.org/sergioamorim/tasiap_backup)
[![Coverage Status](https://coveralls.io/repos/github/sergioamorim/tasiap_backup/badge.svg?branch=master)](https://coveralls.io/github/sergioamorim/tasiap_backup?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/f1f7e1209bb8a2403964/maintainability)](https://codeclimate.com/github/sergioamorim/tasiap_backup/maintainability)

This is my sunday project, so it's development won't be fast - it will be 
a labor of love though.

This module is still in development and will be incorporated to TASIAp once 
it is mature enough. TASIAp is my main project that I work daily, but it is 
not available publicly yet. The goal of this module is to manage the backups 
of the systems that TASIAp is integrated. 

[Paramiko](https://www.paramiko.org/) is being used by this module. 

### Modules
Currently two internal modules are available: routerboard and ssh_client 
+ **routerboard**: this module is responsible to generate backups from 
Mikrotik's RouterBoards. It has functions to generate backups using the 
builtin backup mechanism from the routerboard as well as rsc script files 
from the export command - deployed; 
+ **myauth**: has functions to retrieve MyAuth backups over sftp, to detect 
anomalies on the backup files and to delete old backups from the server - 
deployed;
+ **ssh_client**: the goal of this module is to create ssh connections to 
serve as a tool which other modules can use (as the routerboard module 
mentioned above) - deployed. 

### Feedback
If you found a bug or got any difficulties or questions about this module, 
please 
[open an issue here](https://github.com/sergioamorim/tasiap_backup/issues). 
