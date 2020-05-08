"""Functions to ease interacting with shell calls

Provides various ways to interact with the shell, between calling a command to
finish, calling a command and attaching the current shell to it, capturing the
output of a command, or just checking if a command lives in the $PATH.
"""
import distutils.spawn  # pylint: disable=no-name-in-module,import-error
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from click import ClickException

from den import log

logger = log.get_logger(__name__)

STDOUT = 1
STDERR = 2
ALL = STDOUT | STDERR

if hasattr(subprocess, "DEVNULL"):
    DEVNULL = getattr(subprocess, "DEVNULL")
else:
    DEVNULL = os.open(os.devnull, os.O_RDWR)  # Taken from the 3.x codebase


class CommandFailure(ClickException):
    """Exception thrown by ::run function if `suppress` is turned off

    Wraps up the definition of a failed command run into an exception and
    provides a basic summary of the exit condition and command that failed for
    exception raising.
    """

    def __init__(self, cmd: str, exitcode: int) -> None:
        msg = "command: {} failed with {!s}".format(cmd, exitcode)
        ClickException.__init__(self, msg)


def run(  # pylint: disable=too-many-arguments
    cmd: str,
    interactive: bool = False,
    quiet: int = 0,
    cwd: Optional[Union[Path, str]] = None,
    env: Optional[Dict[str, str]] = None,
    wait: bool = True,
    suppress: bool = False,
) -> Union[int, subprocess.Popen]:
    """Run the command in a subprocess shell

    Can be configured how the command is handled with quietting the stderr or
    stdout output streams (defaults to the current shell's), running it
    interactively (which hooks all three of the current stdin, stdout, and
    stderr to the command), set additional environment variables, change the
    current directory of the command, and whether to wait for the command to
    finish.
    """
    cmd = re.sub(" +", " ", cmd)  # Remove extraneous whitespace
    if interactive:  # don't quiet the output streams interactively
        logger.debug("Running command `%s` interactively.", cmd)
        quiet = 0
        wait = True
    else:
        logger.debug("Running command `%s`.", cmd)

    action = subprocess.Popen(
        cmd.split(" "),
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

    if action.returncode:
        logger.error("Command `%s` failed.", cmd)
        raise CommandFailure(cmd, action.returncode)

    return action.returncode


def output(cmd: str, **kwargs: Any) -> List[str]:
    """Run the supplied command and return the lines of output."""
    std_output = "\n".join(subprocess.check_output(cmd.split(" "), **kwargs))
    assert isinstance(std_output, str)
    return std_output.strip().split("\n")


# NOTE: this is not the best option, but works for 2.7, shutils.which is
#       preferred but is only in 3.3+
def is_installed(command: str) -> Optional[str]:
    """Checks if the specified executable exists on the path

    Useful for checking install dependencies or giving better feedback on a
    command failure (because the executable doesn't exist) instead of a generic
    failure message.
    """
    return distutils.spawn.find_executable(command)  # pylint: disable=no-member
