"""Extensions of click objects

Just a collection of extensions made to add additional functionality to click
objects.
"""
import click


def find_unique_short(group, context, command_name):
    possible_commands = [command for command in group.list_commands(context)
                         if command.startswith(command_name)]

    if len(possible_commands) == 0:
        return None
    elif len(possible_commands) == 1:
        return click.Group.get_command(group, context, possible_commands[0])
    else:
        return possible_commands


class SmartGroup(click.Group):
    """Extended Group with some intelligent additions

    Collection of extended functionality added to the default `Group` object.
    """
    def get_command(self, context, command_name):
        command = click.Group.get_command(self, context, command_name)
        if command is not None:
            return command

        command = find_unique_short(self, context, command_name)
        if type(command) is list:
            context.fail(
                "`{}` is ambiguous and matched multiple commands: {}".format(
                    command_name, ", ".join(command)))

        return command
