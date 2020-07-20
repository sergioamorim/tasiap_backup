## tasiap_backup
This is my sunday project, so it's development won't be fast - it will be 
a labor of love though.

This module is still in development and will be incorporated to TASIAp once it 
is mature enough. TASIAp is my main project that I work daily, but it is 
not available publicly yet. The goal of this module is to manage the backups 
of the systems that TASIAp is integrated. 

[Paramiko](https://www.paramiko.org/) is being used by this module.

### Modules
Currently two internal modules are available: routerboard and ssh_client 
+ **routerboard**: this module is responsible to generate backups from Mikrotik's 
RouterBoards. It has functions to generate backups using the builtin backup 
mechanism from the routerboard as well as rsc script files from the export 
command;
+ **ssh_client**: the goal of this module is to create ssh connections to serve 
as a tool which other modules can use (as the routerboard module mentioned 
above). 

### Feedback
If you found a bug or got any difficulties or questions about this module, 
please 
[open an issue here](https://github.com/sergioamorim/tasiap_backup/issues). 
