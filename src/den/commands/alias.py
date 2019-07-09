"""Add in support for command aliasing

Aliasing is a configuration based system for creating short hand subcommands
that reference a full command and execute it when the alias is used.  These
aliases will live in configs under a specific section and consist of a defined
pair of the `alias` -> `expanded command`.  For example::

    [alias]
    crst = create --start

This would create an alias so that if you run `den crst` it would be the
equivalent of running `den create --start`.

Additional commands exist to interact with the aliases, but they are basically
re-wraps of the `config` group of commands.
"""
import os
from typing import List, Optional, Tuple

import click

from den import LOCAL_CONFIG_FILE, USER_CONFIG_FILE
from den.click_ext import SmartGroup
from den.commands.config import (
    MissingConfigurationException,
    get_value,
    set_value,
)
from den.context import Context

ALIAS_SECTION = "alias"
__commands__ = ["interact_alias"]
ALIAS_OUTPUT_FORMAT = "`den {key}` is aliased to `den {value}`"


def find(context: Context, alias: str) -> Optional[List[str]]:
    """Lookup command alias

    Retrieves the expanded command when provided with the application context
    and the alias desired.  Will return `None` if no alias is defined.
    """
    if not hasattr(context, "config"):
        return None

    expansion = context.config.get(ALIAS_SECTION, alias)
    return expansion.split(" ") if expansion else None


class AliasGroup(SmartGroup):
    """Extended SmartGroup with aliasing support

    Adds in logic to command resolution to perform an alias look up if the
    command does not normally resolve.  This means that if an alias is defined
    that overlaps with an existing command, it will never be run.
    """

    def resolve_command(
        self, ctx: click.Context, args: List[str]
    ) -> Tuple[str, click.Command, List[str]]:
        try:
            return click.Group.resolve_command(self, ctx, args)
        except click.ClickException:
            alias = find(ctx.obj, args[0])
            if not alias:
                raise
            return click.Group.resolve_command(self, ctx, alias + args[1:])
            # the `alias + args[1:]` allows for the expanded alias to append
            # the extra arguments to itself, treating it like an inline
            # expansion


class NoAliasException(click.ClickException):
    """Exception raised when an alias lookup fails. """

    def __init__(self, alias: str) -> None:
        click.ClickException.__init__(
            self, "No `{}` alias " "defined.".format(alias)
        )


# > den alias <alias> [<command>]
@click.command("alias", short_help="Create or modify command aliases")
@click.option(
    "-u",
    "--user",
    is_flag=True,
    default=False,
    help="Use the user level configuration.",
)
@click.argument("alias")  # alias to act on
@click.argument("command", nargs=-1, required=False)  # optional command to set
@click.pass_context
def interact_alias(
    context: click.Context, user: bool, alias: str, command: List[str]
) -> None:
    """Check, modify, or create command aliases

    If a command is provided, will set the alias to the command, if it is not
    provided will report the expaned command the alias refers to.  An alias
    acts as a command expansion: `den alias crst -- create --start` would mean
    that `den crst` would be expanded to `den create --start`.
    """
    context.obj.target_config = (
        os.path.expanduser(USER_CONFIG_FILE)
        if user
        else os.path.join(context.obj.cwd, LOCAL_CONFIG_FILE)
    )

    if command:
        context.invoke(
            set_value, section=[ALIAS_SECTION, alias], value=" ".join(command)
        )
    else:
        try:
            context.invoke(
                get_value,
                section=ALIAS_SECTION,
                key=alias,
                output_format=ALIAS_OUTPUT_FORMAT,
            )
        except MissingConfigurationException:
            raise NoAliasException(alias)
