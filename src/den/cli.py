"""
Defines the top level CLI object for den, this is in conjunction with the
click_ext module for dictating and configuring the top level click handler.
"""
import logging
import os

import click
import docker as _docker

from den import CONFIG_FILES, CONTEXT_SETTINGS, log, utils
from den.__version__ import __version__
from den.commands.alias import AliasGroup
from den.config import Config

logger = log.get_logger("den")


class Context:
    """Cached context collector for commands

    Meant to provide lazy definitions for various contextually shared objects
    that commands will want without the specifics of their instantiation or
    definition being distributed among the commands.
    """

    debug: bool

    @utils.cached_property
    def config(self) -> Config:  # pylint: disable=no-self-use
        """(cached property) Contextual configuration"""
        return Config(*CONFIG_FILES)

    @utils.cached_property
    def cwd(self) -> str:  # pylint: disable=no-self-use
        """(cached property) Determined root directory"""
        return utils.base_dir(".git", ".den.ini")

    @utils.cached_property
    def docker(self) -> _docker.DockerClient:  # pylint: disable=no-self-use
        """(cached property) Docker client interface"""
        return _docker.from_env()

    @utils.cached_property
    def default_name(self) -> str:
        """(cached property) inferred project name"""
        return os.path.basename(self.cwd)


@click.group("den", context_settings=CONTEXT_SETTINGS, cls=AliasGroup)
@click.option("-v", "--verbose", count=True, help="Set verbose logging")
@click.option("-d", "--debug", is_flag=True, default=False)
@click.pass_obj
def den(context: Context, verbose: int, debug: bool) -> None:
    """Easy development environments aka development dens"""
    verbose = (
        verbose
        if verbose
        else int(context.config.get("default", "verbosity", "0"))
    )
    debug = debug if debug else context.config.get("default", "debug")

    if debug:
        verbose = logging.DEBUG

    logger.setup(verbose)
    context.debug = debug

    if debug:
        logger.debug("Running in debug mode")


@den.command("version", short_help="Return the version of the installed den")
def version() -> None:
    """Subcommand for giving the version number."""
    logger.echo("Den version {}".format(__version__))


def run() -> None:
    """Setup and execute the top level click group."""
    utils.bind_module("den.commands.dens", den)
    utils.bind_module("den.commands.config", den)
    utils.bind_module("den.commands.alias", den)
    return den(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        obj=Context()
    )
