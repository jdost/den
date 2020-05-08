"""Configuration control commands

These are to allow a CLI system for reading and writing to the config files.
There are two targets for each action, the default "local" config and the
"user" config (which lives in the user's home).
"""
import configparser
import contextlib
import os.path
from typing import Generator, Optional, Tuple

import click

from den import LOCAL_CONFIG_FILE, USER_CONFIG_FILE, log
from den.click_ext import SmartGroup
from den.context import Context

__commands__ = ["config_group"]
logger = log.get_logger(__name__)

GET_OUTPUT_FORMAT = "{section}.{key} = {value}"


class MissingConfigurationException(click.ClickException):
    """Exception raised on misses in config lookups, meant to collect error
    display logic for various failure conditions.
    """

    def __init__(self, section: str, key: Optional[str] = None) -> None:
        msg = (
            "No `{}` section defined.".format(section)
            if not key
            else "No `{}.{}` option defined.".format(section, key)
        )
        click.ClickException.__init__(self, msg)


def _expand(
    section: str, key: Optional[str] = None, key_required: bool = True
) -> Tuple[str, Optional[str]]:
    """Section//Key expansion utility

    Will get the section and key target in a config from the provided values.
    This will be the two values if they are defined, expanding the `section`
    value if it is of the `section.key` format, or falling back to a configured
    style (either failing or returning just the section).
    """
    if not key and "." not in section:
        if key_required:
            raise click.BadParameter(
                "You need to specify a section and a key "
                "(or `section.key`).",
                param_hint="SECTION [KEY]",
            )

        return section, None

    if not key:
        section, key = section.split(".", 1)

    return section, key


@contextlib.contextmanager
def _modify_config(
    config_file: str,
) -> Generator[configparser.ConfigParser, None, None]:
    """Config modification context

    Allows for creating a temporary `ConfigParser` to modify and then save the
    newly modified config file.
    """
    parser = configparser.ConfigParser()
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            if hasattr(parser, "read_file"):
                getattr(parser, "read_file")(f)
            else:
                getattr(parser, "readfp")(f)

    yield parser

    with open(config_file, "w") as f:
        parser.write(f)


CONFIG_HELP = """Interact with the den configuration values

By default, looks at the "local" configuration file (located at {}) for
interactions.  If the "user" configuration file is chosen, will use the file
located at {} instead.
""".format(
    LOCAL_CONFIG_FILE, USER_CONFIG_FILE
)

# > den config <...>
@click.group(
    "config",
    help=CONFIG_HELP,
    cls=SmartGroup,
    short_help="Modify and view configuration values",
)
@click.option(
    "-u",
    "--user",
    is_flag=True,
    default=False,
    help="Use the user level configuration.",
)
@click.pass_obj
def config_group(context: Context, user: bool) -> None:
    """Group for config interactions.
    """
    context.target_config = (
        os.path.expanduser(USER_CONFIG_FILE)
        if user
        else os.path.join(context.cwd, LOCAL_CONFIG_FILE)
    )


# > den config get <section> [<key>]
@config_group.command("get", short_help="Lookup configuration value(s)")
@click.argument("section")  # Name of section to get
@click.argument("key", required=False, default=None)  # Name of the key
@click.pass_obj
def get_value(
    context: Context,
    section: str,
    key: Optional[str],
    output_format: str = GET_OUTPUT_FORMAT,
) -> None:
    """Retrieve the value in a config

    Will return all values under SECTION if just SECTION is defined, otherwise
    will just return the value for SECTION.KEY.
    """
    section, key = _expand(section, key, key_required=False)

    parser = configparser.ConfigParser()
    assert isinstance(context.target_config, str)
    parser.read(context.target_config)

    try:
        if key:
            value = parser.get(section, key)
            logger.echo(
                output_format.format(section=section, key=key, value=value)
            )
        else:
            for k, v in parser.items(section):
                logger.echo(
                    output_format.format(section=section, key=k, value=v)
                )
    except configparser.NoSectionError:
        raise MissingConfigurationException(section)
    except configparser.NoOptionError:
        raise MissingConfigurationException(section, key)


# > den config set <section> [<key>] <value>
@config_group.command("set", short_help="Define a new configuration value")
@click.argument(
    "section", nargs=-1, metavar="SECTION [KEY]"
)  # Name of section to get
@click.argument("value", default=None)
@click.pass_obj
def set_value(context: Context, section: str, value: str) -> None:
    """Set a config value

    Sets the SECTION.KEY config value to VALUE and saves the file.
    """
    section, key = _expand(*section)
    assert isinstance(context.target_config, str)
    assert key is not None

    with _modify_config(context.target_config) as parser:
        if not parser.has_section(section):
            parser.add_section(section)

        parser.set(section, key, value)


# > den config rm <section> [<key>]
@config_group.command("rm", short_help="Delete configuration value(s)")
@click.argument("section")  # Name of the section
@click.argument("key", required=False, default=None)  # Name of the key
@click.pass_obj
def delete(context: Context, section: str, key: str) -> None:
    """Remove a config value or section

    If a KEY is not provided, the entire SECTION will be removed.
    """
    target = _expand(section, key, key_required=False)
    assert isinstance(context.target_config, str)
    if target[1] is None:
        click.confirm(
            "This will delete the entire `{}` " "section.".format(target[0]),
            abort=True,
            default=True,
        )

    with _modify_config(context.target_config) as parser:
        if target[1] is not None:
            logger.echo("Removing {}.{}.".format(*target))
            parser.remove_option(target[0], target[1])
        else:
            parser.remove_section(target[0])
