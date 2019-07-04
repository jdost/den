"""Base definition for CLI application

Defines the top level command group, shared application context, sets up the
logging level, and defines the command modules to bind to the base group
definition.

Config settings::
    [default]
    debug=1  # equivalent to the `-d`//`--debug` flag on all calls
    verbosity=N  # equivalent to the number of `-v` flags set on all calls
"""
import click

import den.utils as utils

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
LOCAL_CONFIG_FILE = ".den.ini"
USER_CONFIG_FILE = (click.get_app_dir("den") + ".ini").replace(utils.HOME, "~")
CONFIG_FILES = [LOCAL_CONFIG_FILE, USER_CONFIG_FILE]


def main() -> None:
    """Setup and call of the object"""
    import den.cli as cli

    cli.run()


if __name__ == "__main__":
    main()
