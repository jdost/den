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
import docker
import os.path
import log
import utils

from config import Config

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}
LOCAL_CONFIG_FILE = ".den.ini"
USER_CONFIG_FILE = (click.get_app_dir("den") + ".ini").replace(utils.HOME, "~")
CONFIG_FILES = [LOCAL_CONFIG_FILE, USER_CONFIG_FILE]


class Context(object):
    """Cached context collector for commands

    Meant to provide lazy definitions for various contextually shared objects
    that commands will want without the specifics of their instantiation or
    definition being distributed among the commands.
    """
    @utils.cached_property
    def config(self):
        return Config(*CONFIG_FILES)

    @utils.cached_property
    def cwd(self):
        return utils.base_dir(".git", ".den.ini")

    @utils.cached_property
    def docker(self):
        return docker.from_env()

    @utils.cached_property
    def default_name(self):
        return os.path.basename(self.cwd)


from commands.alias import AliasGroup

@click.group("den", context_settings=CONTEXT_SETTINGS, cls=AliasGroup)
@click.option("-v", "--verbose", count=True, help="Set verbose logging")
@click.option("-d", "--debug", is_flag=True, default=False)
@click.pass_obj
def den(context, verbose, debug):
    """Easy development environments aka development dens"""
    if not verbose:
        verbose = int(context.config.get("default", "verbosity", "0"))
    if not debug:
        debug = context.config.get("default", "debug")

    if debug:
        verbose = log.DEBUG
    elif verbose:
        pass

    log.set_level(verbose)
    context.debug = debug


def main():
    """Setup and call of the object"""
    utils.bind_module("den.commands.dens", den)
    utils.bind_module("den.commands.config", den)
    utils.bind_module("den.commands.alias", den)
    den(obj=Context())


if __name__ == "__main__":
    main()
