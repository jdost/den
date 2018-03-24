"""Base definition for CLI application

Defines the top level command group, shared application context, sets up the
logging level, and defines the command modules to bind to the base group
definition.

Config settings::
    [default]
    debug=1  # equivalent to the `-d`//`--debug` flag on all calls
    verbosity=N  # equivalent to the number of `-v` flags set on all calls
"""
import os.path

import click
import docker

import den.log as log
import den.utils as utils

from den.config import Config

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}
LOCAL_CONFIG_FILE = ".den.ini"
USER_CONFIG_FILE = (click.get_app_dir("den") + ".ini").replace(utils.HOME, "~")
CONFIG_FILES = [LOCAL_CONFIG_FILE, USER_CONFIG_FILE]
__version__ = "0.1"

from den.commands.alias import AliasGroup  # pylint: disable=wrong-import-position

class Context(object):
    """Cached context collector for commands

    Meant to provide lazy definitions for various contextually shared objects
    that commands will want without the specifics of their instantiation or
    definition being distributed among the commands.
    """
    @utils.cached_property
    def config(self):  # pylint: disable=no-self-use
        """(cached property) Contextual configuration"""
        return Config(*CONFIG_FILES)

    @utils.cached_property
    def cwd(self):  # pylint: disable=no-self-use
        """(cached property) Determined root directory"""
        return utils.base_dir(".git", ".den.ini")

    @utils.cached_property
    def docker(self):  # pylint: disable=no-self-use
        """(cached property) Docker client interface"""
        return docker.from_env()

    @utils.cached_property
    def default_name(self):
        """(cached property) inferred project name"""
        return os.path.basename(self.cwd)

@click.group("den", context_settings=CONTEXT_SETTINGS, cls=AliasGroup)
@click.option("-v", "--verbose", count=True, help="Set verbose logging")
@click.option("-d", "--debug", is_flag=True, default=False)
@click.pass_obj
def den(context, verbose, debug):
    """Easy development environments aka development dens"""
    verbose = verbose if verbose else \
            int(context.config.get("default", "verbosity", "0"))
    debug = debug if debug else context.config.get("default", "debug")

    if debug:
        verbose = log.DEBUG

    log.set_level(verbose)
    context.debug = debug

    if debug:
        log.debug("Running in debug mode")


@den.command("version", short_help="Return the version of the installed den")
def version():
    log.echo("Den version {}".format(__version__))


def main():
    """Setup and call of the object"""
    utils.bind_module("den.commands.dens", den)
    utils.bind_module("den.commands.config", den)
    utils.bind_module("den.commands.alias", den)
    return den(obj=Context())  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg


if __name__ == "__main__":
    main()
