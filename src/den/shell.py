"""Functions to ease interacting with shell calls

Provides various ways to interact with the shell, between calling a command to
finish, calling a command and attaching the current shell to it, capturing the
output of a command, or just checking if a command lives in the $PATH.
"""
import distutils.spawn
import os
import subprocess
import sys
import utils

from click import ClickException

STDOUT = 1
STDERR = 2
ALL = STDOUT | STDERR
DEVNULL = os.open(os.devnull, os.O_RDWR)  # Taken from the 3.x codebase


class CommandFailure(ClickException):
    """Exception thrown by ::run function if `suppress` is turned off

    Wraps up the definition of a failed command run into an exception and
    provides a basic summary of the exit condition and command that failed for
    exception raising.
    """
    def __init__(self, cmd, exitcode):
        msg = "command: {} failed with {!s}".format(cmd, exitcode)
        ClickException.__init__(self, msg)


def run(cmd, interactive=False, quiet=0, cwd=None, env=None, wait=True, suppress=False):
    """Run the command in a subprocess shell

    Can be configured how the command is handled with quietting the stderr or
    stdout output streams (defaults to the current shell's), running it
    interactively (which hooks all three of the current stdin, stdout, and
    stderr to the command), set additional environment variables, change the
    current directory of the command, and whether to wait for the command to
    finish.
    """
    if interactive:  # don't quiet the output streams interactively
        quiet=0

    action = subprocess.Popen(
        cmd.split(' '),
        cwd=cwd,
        env=env,
        stdin=sys.stdin if interactive else None,
        stdout=DEVNULL if quiet & STDOUT else sys.stdout,
        stderr=DEVNULL if quiet & STDERR else sys.stderr,
    )

    if not wait:
        return action

    action.wait()
    if suppress:
        return action.returncode
    elif action.returncode:
        raise CommandFailure(cmd, action.returncode)
    else:
        return action.returncode


def output(cmd, **kwargs):
    """Run the supplied command and return the lines of output."""
    return subprocess.check_output(cmd.split(' '), **kwargs)\
            .strip().split('\n')


# NOTE: this is not the best option, but works for 2.7, shutils.which is
#       preferred but is only in 3.3+
def is_installed(command):
    """Checks if the specified executable exists on the path

    Useful for checking install dependencies or giving better feedback on a
    command failure (because the executable doesn't exist) instead of a generic
    failure message.
    """
    return distutils.spawn.find_executable(command)
