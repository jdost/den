"""Extensions of click objects

Just a collection of extensions made to add additional functionality to click
objects.
"""
import click


def find_unique_short(group, context, command_name):
    """Shorthand resolution
    Attempt to determine a shorthand expansion for a command, this will try and
    see if there is a unique command that starts with the `command_name` value
    and return it if there is, otherwise will return the options (`None` for
    a complete miss).
    """
    possible_commands = [
        command
        for command in group.list_commands(context)
        if command.startswith(command_name)
    ]

    if len(possible_commands) == 1:
        return click.Group.get_command(group, context, possible_commands[0])

    return possible_commands if possible_commands else None


class SmartGroup(click.Group):
    """Extended Group with some intelligent additions

    Collection of extended functionality added to the default `Group` object.
    """

    def get_command(self, ctx, cmd_name):
        command = click.Group.get_command(self, ctx, cmd_name)
        if command is not None:
            return command

        command = find_unique_short(self, ctx, cmd_name)
        if isinstance(command, list):
            ctx.fail(
                "`{}` is ambiguous and matched multiple commands: {}".format(
                    cmd_name, ", ".join(command)
                )
            )

        return command
