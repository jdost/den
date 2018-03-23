"""Log output wrapper

Wraps log output to allow for dictating log levels and provide some helpers for
pretty printing output to the command line.
"""
import contextlib
import re
import sys

from functools import partial

import click

from colorama import Fore, init

init()

def _clrd(color, msg):
    """Generated a clean foreground colored message"""
    return getattr(Fore, color) + msg + Fore.RESET

SUBSTITUTIONS = [
    (re.compile(r"\`([^\`]*)\`"), Fore.CYAN + r"\1" + Fore.RESET),
]
OUTPUT, ERROR, WARN, INFO, DEBUG = range(5)
LEVEL = OUTPUT
LEVELS = {
    ERROR: _clrd("RED", "ERROR"),
    WARN: _clrd("YELLOW", "WARN"),
    INFO: _clrd("GREEN", "INFO"),
    DEBUG: _clrd("WHITE", "DEBUG"),
}


def _format(msg):
    """Format message using clean substitutions

    These use some colorama options to fix emphasis or other markings for a
    richer output format.
    """
    for pattern, replace in SUBSTITUTIONS:
        msg = re.sub(pattern, replace, msg)
    return msg


def echo(msg, level=OUTPUT, **kwargs):
    """Wrapper for `click.echo` with formatting

    Uses the consolidated `format` function to apply some cleaning output
    filters.
    """
    if level > LEVEL:
        return
    if level is not OUTPUT:
        msg = "{} - {}".format(LEVELS[level], msg)
    click.echo(_format(msg), **kwargs)

# Shorthand partials to default the level argument
error = partial(echo, level=ERROR)  # pylint: disable=invalid-name
warn = partial(echo, level=WARN)  # pylint: disable=invalid-name
info = partial(echo, level=INFO)  # pylint: disable=invalid-name
debug = partial(echo, level=DEBUG)  # pylint: disable=invalid-name


def set_level(level=OUTPUT):
    """Define the global logging level."""
    global LEVEL  # pylint: disable=global-statement
    LEVEL = level


@contextlib.contextmanager
def report_success(msg, debug=None, abort=True):  # pylint: disable=redefined-outer-name
    """Context wrapper for reporting success of a step

    Prints the step text and then a success or failure suffix depending on if
    the context raised an error or not.
    """
    click.echo(_format(msg) + "...", nl=(LEVEL != OUTPUT))
    try:
        yield
        if LEVEL == OUTPUT:
            click.echo(_clrd("GREEN", "done"))
    except click.ClickException:
        if LEVEL == OUTPUT:
            click.echo(_clrd("RED", "error"))
        if debug or LEVEL == DEBUG:
            raise
        if abort:
            sys.exit(1)
