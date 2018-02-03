"""Configuration control commands

These are to allow a CLI system for reading and writing to the config files.
There are two targets for each action, the default "local" config and the
"user" config (which lives in the user's home).
"""
import click
import ConfigParser
import contextlib
import os.path

from .. import LOCAL_CONFIG_FILE, USER_CONFIG_FILE
from ..click_ext import SmartGroup

__commands__ = ["config_group"]

GET_OUTPUT_FORMAT = "{section}.{key} = {value}"


class MissingConfigurationException(click.ClickException):
    def __init__(self, section, key=None):
        msg = "No `{}` section defined.".format(section) if not key \
                else "No `{}.{}` option defined.".format(section, key)
        click.ClickException.__init__(self, msg)


def _expand(section, key=None, key_required=True):
    """Section//Key expansion utility

    Will get the section and key target in a config from the provided values.
    This will be the two values if they are defined, expanding the `section`
    value if it is of the `section.key` format, or falling back to a configured
    style (either failing or returning just the section).
    """
    if not key and "." not in section:
        if key_required:
            raise click.BadParameter("You need to specify a section and a key "
                                     "(or `section.key`).",
                                     param_hint="SECTION [KEY]")
        else:
            return section, None
    elif not key:
        section, key = section.split(".", 1)

    return section, key


@contextlib.contextmanager
def _modify_config(config_file):
    """Config modification context

    Allows for creating a temporary `ConfigParser` to modify and then save the
    newly modified config file.
    """
    parser = ConfigParser.ConfigParser()
    with open(config_file, "r") as f:
        parser.readfp(f)

    yield parser

    with open(config_file, "w") as f:
        parser.write(f)


CONFIG_HELP = """Interact with the den configuration values

By default, looks at the "local" configuration file (located at {}) for
interactions.  If the "user" configuration file is chosen, will use the file
located at {} instead.
""".format(LOCAL_CONFIG_FILE, USER_CONFIG_FILE)

# > den config <...>
@click.group("config", help=CONFIG_HELP, cls=SmartGroup,
             short_help="Modify and view configuration values")
@click.option("-u", "--user", is_flag=True, default=False,
              help="Use the user level configuration.")
@click.pass_obj
def config_group(context, user):
    """Group for config interactions.
    """
    context.target_config = os.path.expanduser(USER_CONFIG_FILE) if user \
            else os.path.join(context.cwd, LOCAL_CONFIG_FILE)


# > den config get <section> [<key>]
@config_group.command("get", short_help="Lookup configuration value(s)")
@click.argument("section")  # Name of section to get
@click.argument("key", required=False, default=None)  # Name of the key
@click.pass_obj
def get_value(context, section, key):
    """Retrieve the value in a config

    Will return all values under SECTION if just SECTION is defined, otherwise
    will just return the value for SECTION.KEY.
    """
    section, key = _expand(section, key, key_required=False)

    parser = ConfigParser.ConfigParser()
    parser.read(context.target_config)

    try:
        if key:
            value = parser.get(section, key)
            click.echo(GET_OUTPUT_FORMAT.format(**locals()))
        else:
            for key, value in parser.items(section):
                click.echo(GET_OUTPUT_FORMAT.format(**locals()))
    except ConfigParser.NoSectionError:
        raise MissingConfigurationException(section)
    except ConfigParser.NoOptionError:
        raise MissingConfigurationException(section, key)

# > den config set <section> [<key>] <value>
@config_group.command("set", short_help="Define a new configuration value")
@click.argument("section", nargs=-1, metavar="SECTION [KEY]")  # Name of section to get
@click.argument("value", default=None)
@click.pass_obj
def set_value(context, section, value):
    """Set a config value

    Sets the SECTION.KEY config value to VALUE and saves the file.
    """
    section, key = _expand(*section)

    with _modify_config(context.target_config) as parser:
        if not parser.has_section(section):
            parser.add_section(section)

        parser.set(section, key, value)

# > den config rm <section> [<key>]
@config_group.command("rm", short_help="Delete configuration value(s)")
@click.argument("section")  # Name of the section
@click.argument("key", required=False, default=None)  # Name of the key
@click.pass_obj
def delete(context, section, key):
    """Remove a config value or section

    If a KEY is not provided, the entire SECTION will be removed.
    """
    section, key = _expand(section, key, key_required=False)
    if not key:
        click.confirm("This will delete the entire `{}` "
                      "section.".format(section), abort=True, default=True)

    with _modify_config(context.target_config) as parser:
        if key:
            click.echo("Removing {}.{}.".format(section, key))
            parser.remove_option(section, key)
        else:
            parser.remove_section(section)
