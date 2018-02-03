import click
import contextlib
import re
import sys

from colorama import Fore, init
from functools import partial

init()

SUBSTITUTIONS = [
    (re.compile(r"\`([^\`]*)\`"), Fore.CYAN + r"\1" + Fore.RESET),
]
OUTPUT, ERROR, WARN, INFO, DEBUG = range(5)
LEVEL = OUTPUT
LEVELS = {
    ERROR: Fore.RED + "ERROR" + Fore.RESET,
    WARN: Fore.YELLOW + "WARN" + Fore.RESET,
    INFO: Fore.GREEN + "INFO" + Fore.RESET,
    DEBUG: Fore.WHITE + "DEBUG" + Fore.RESET,
}


def format(msg):
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
    click.echo(format(msg), **kwargs)

# Shorthand partials to default the level argument
error = partial(echo, level=ERROR)
warn = partial(echo, level=WARN)
info = partial(echo, level=INFO)
debug = partial(echo, level=DEBUG)


def set_level(level=OUTPUT):
    """Define the global logging level."""
    global LEVEL
    LEVEL = level


@contextlib.contextmanager
def report_success(msg, debug=None, abort=True):
    """Context wrapper for reporting success of a step

    Prints the step text and then a success or failure suffix depending on if
    the context raised an error or not.
    """
    click.echo(format(msg) + "...", nl=(LEVEL != OUTPUT))
    try:
        yield
        if LEVEL == OUTPUT:
            click.echo("done")
    except:
        if LEVEL == OUTPUT:
            click.echo("error")
        if debug or LEVEL == DEBUG:
            raise
        if abort:
            sys.exit(1)
