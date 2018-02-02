import click
import docker
import os.path
import utils

from config import Config
from click_ext import SmartGroup

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}
CONFIG_FILES = [".den.ini", "~/.config/den.ini", "~/.den.ini"]


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


@click.group("den", context_settings=CONTEXT_SETTINGS, cls=SmartGroup)
def den():
    """Easy development environments aka development dens"""
    pass


def main():
    """Setup and call of the object"""
    utils.bind_module("den.commands.dens", den)
    den(obj=Context())


if __name__ == "__main__":
    main()
