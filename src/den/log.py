"""Log output wrapper

Wraps log output to allow for dictating log levels and provide some helpers for
pretty printing output to the command line.
"""
import contextlib
import logging
import re
import sys

import click

from colorama import Fore, init

init()

SUBSTITUTIONS = [
    (re.compile(r"\`([^\`]*)\`"), Fore.CYAN + r"\1" + Fore.RESET),
]
CODE_COLOR = Fore.CYAN
VERBOSITY_LEVEL = [
    logging.CRITICAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
]


def _format(msg):
    """Format message using clean substitutions

    These use some colorama options to fix emphasis or other markings for a
    richer output format.
    """
    for pattern, replace in SUBSTITUTIONS:
        msg = re.sub(pattern, replace, msg)
    return msg


class ClickFormatter(logging.Formatter):
    """Click specific formatter to allow nice console output

    Plugs into the built in logging module and allows for some nicer CLI output
    to stdout.
    """
    DEFAULT_FORMAT = "%(levelname)s - %(message)s"
    DEBUG_FORMAT = "%(levelname)s:%(name)s(%(pathname)s:%(lineno)d) - %(message)s"
    COLORS = {
        logging.CRITICAL: Fore.RED,
        logging.ERROR: Fore.RED,
        logging.WARNING: Fore.YELLOW,
        logging.INFO: Fore.GREEN,
        logging.DEBUG: Fore.WHITE,
    }
    ALIASES = {
        logging.CRITICAL: "CRIT",
        logging.ERROR: "ERR",
        logging.WARNING: "WARN",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
    }

    def __init__(self, fmt=None, **kwargs):
        if not fmt:
            fmt = self.DEFAULT_FORMAT

        logging.Formatter.__init__(self, fmt=fmt, **kwargs)

    def format(self, record):
        """Performs nicer console output formatting for the output message
        """
        msg = _format(record.getMessage())
        record.getMessage = lambda: msg
        record.levelname = (
            self.COLORS[record.levelno] +
            self.ALIASES[record.levelno] +
            Fore.RESET
        )
        return logging.Formatter.format(self, record)


class ClickLogger(logging.Logger):
    """Extends and defaults the logging output

    Useful to pass extensions for output beyond this module using the
    `logging` framework.
    """
    def __init__(self, *args, **kwargs):
        logging.Logger.__init__(self, *args, **kwargs)

        output_handler = logging.StreamHandler(sys.stdout)
        output_handler.setFormatter(ClickFormatter())
        self.addHandler(output_handler)
        self.propagate = 0

    @classmethod
    def echo(cls, msg):
        """Simple print wrapper for nicer shell output
        """
        click.echo(_format(msg))

    @contextlib.contextmanager
    def report_success(self, msg, debug=None, abort=True):  # pylint: disable=redefined-outer-name
        """Context wrapper for reporting success of a step

        Prints the step text and then a success or failure suffix depending on if
        the context raised an error or not.
        """
        click.echo(_format(msg) + "...", nl=self.level == logging.DEBUG)
        try:
            yield
            click.echo(Fore.GREEN + "done" + Fore.RESET)
        except click.ClickException:
            click.echo(Fore.RED + "error" + Fore.RESET)
            if debug:
                raise
            if abort:
                sys.exit(1)
