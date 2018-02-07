## Den command set collection

Each file in here is a "command set", basically just a collection of commands for
den that dictate a shared focus.  The commands are all built using `click` and the
top level commands are defined using the `__commands__` variable.  This is what gets
used when the module is bound to the parent command (in this case `den`).

### Adding your own

You can define a new file in here, take a look at some of the existing ones for 
examples of how they are built.  You basically define the function that should be
run, then using decorators define how that function gets built from the command 
line.  This means what the action command looks like, argument definitions and how
the function gets called by it's parent.  The one thing to look for is using the
`click.pass_obj` decorator.  This will provide the application's shared context 
object as the first argument, this holds objects for interacting with the docker 
API, reading the configuration, and some other shared utilities for the state of the
tool.  Once you want to have the set included in den, just add the definition to the
`main` function in the `__init__.py` in the [root den source 
directory](/src/den/__init__.py).

### dens.py

Collection of commands for controlling the lifecycle of a den container.  This means
creation, starting, stopping, and deleting them.  Other, miscellaneous commands will
live in here until a larger definition of their purpose is ever found to migrate 
into a larger command set (like moving `list` to an information set).

### config.py

Subcommand group under `config` to read, write, and remove information from the 
config files.  The config files are just `ini` formatted files and can be editted
by hand, but this adds a utility if you don't want to have to modify the files.

### alias.py

Mixture of things that define how alias behavior works in `den`.  Aliases are 
basically defined string expansions for the command line.  They are much like git's
where you can define an alias of `co` to map to `checkout` or something more complex
like `lg` mapping to `log --color --graph --abbrev-commit`.  The set defines the
`alias` command which just wraps up commands from the config definition and provides
an expanded definition for how the base command handles misses on command line calls
to fallback to checking for defined aliases.
