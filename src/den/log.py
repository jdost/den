"""Extend the built in logging functionality for CLI output

Extends what the logging module provides, which works well for services, to
act cleanly with a CLI application.  This allows for things to remain pythonic
while getting a nice CLI output behavior
"""
import contextlib
import logging
import re
import sys
from pathlib import Path
from types import TracebackType
from typing import Any, Dict, Iterator, Mapping, Optional, Tuple, Union

import click

_SysExcInfoType = Union[
    Tuple[type, BaseException, Optional[TracebackType]], Tuple[None, None, None]
]
_ExcInfoType = Union[None, bool, _SysExcInfoType, BaseException]


SUBSTITUTIONS = [
    (re.compile(r"\`([^\`]*)\`"), lambda s: click.style(s.group(1), fg="cyan"))
]
LEVEL_LOOKUP = [
    logging.NOTSET,
    logging.CRITICAL,
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
]
CWD = str(Path.cwd())


def _format(msg: str) -> str:
    """Format message using clean substitutions

    These use some colorama options to fix emphasis or other markings for a
    richer output format.
    """
    for pattern, replace in SUBSTITUTIONS:
        msg = re.sub(pattern, replace, msg)
    return msg


class CLIFormatter(logging.Formatter):
    """CLI specific log output formatter

    Performs various ANSI coloring and nice output patterns to allow for a
    simple and rich experience with logging during operation.
    """

    DEFAULT_FORMAT = "%(levelname)s - %(message)s"
    COLORS = {  # Foreground color for each levelname
        logging.CRITICAL: "red",
        logging.ERROR: "red",
        logging.WARNING: "yellow",
        logging.INFO: "green",
        logging.DEBUG: "white",
    }
    ALIASES = {  # Shorthand output alias for each levelname output
        logging.CRITICAL: "CRIT",
        logging.ERROR: "ERR",
        logging.WARNING: "WARN",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
    }

    def __init__(self, fmt: Optional[str] = None, **kwargs: Any) -> None:
        fmt = fmt if fmt is not None else self.DEFAULT_FORMAT
        super().__init__(fmt=fmt, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Custom modification of the LogRecord for CLI output
        """
        record.msg = _format(record.msg)
        record.pathname = str(Path(record.pathname).resolve()).replace(CWD, ".")
        record.levelname = click.style(
            self.ALIASES[record.levelno], fg=self.COLORS[record.levelno]
        )
        return super().format(record)


class CLILogger(logging.Logger):
    """CLI specific logging class

    Wraps the internal logging logic to provide improved functionality for
    logging output using the normal logging system in regards to a CLI
    application.
    """

    _pending_log: bool

    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        self._pending_log = False
        super().__init__(name, level)

    def setLevel(self, level: Union[int, str] = logging.ERROR) -> None:
        """Setup logger level
        """
        assert isinstance(level, int), "Must use integer logging level"
        if level < logging.CRITICAL:  # is not a logging level
            level = (
                LEVEL_LOOKUP[level]
                if level < len(LEVEL_LOOKUP)
                else logging.DEBUG
            )

        return super().setLevel(level)

    def setup(
        self, level: int, formatter: Optional[logging.Formatter] = None
    ) -> None:
        """Helper method for performing some deferred initialization.
        Defines a default handler if one is not setup by default, defines a
        formatter using the CLIFormatter if one is not specified, and
        normalizes the logging level.
        """
        if not self.hasHandlers():
            stdout_output = logging.StreamHandler(sys.stdout)
            stdout_output.setFormatter(
                formatter if formatter is not None else CLIFormatter()
            )
            self.addHandler(stdout_output)

        self.setLevel(level)

    def _log(  # pylint: disable=too-many-arguments
        self,
        level: int,
        msg: Any,
        args: Union[Tuple[Any, ...], Mapping[str, Any]],
        exc_info: _ExcInfoType = None,
        extra: Optional[Dict[str, Any]] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        """Wraps the log caller to allow for tracking if hanging log lines
        should be closed before outputting new messages.  This acts as a
        passthrough with the one goal of printing pending newlines to avoid
        for jumbled log output.
        """
        if self._pending_log:
            click.echo("")
            self._pending_log = False

        # uses the `getattr` call to bypass a lack of type signature for the
        # private _log method
        getattr(super(), "_log")(
            level,
            msg,
            args=args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel,
        )

    @contextlib.contextmanager
    def report_success(self, msg: str) -> Iterator[None]:
        """Context wrapper for reporting success of a step

        Prints the step text and then a success or failure suffix depending on
        if the context raised an error or not.
        """
        click.echo(
            _format(msg) + "...",
            nl=(self.getEffectiveLevel() < logging.WARNING),
        )
        CLILogger._pending_log = True
        try:
            yield
            click.secho("done", fg="green")
        except Exception:
            if CLILogger._pending_log:
                click.secho("error", fg="red")
            raise

    @staticmethod
    def echo(msg: str, *args: Optional[str]) -> None:
        """Simple output to stdout with formatting helpers applied."""
        click.echo(_format(msg % args))


logging.setLoggerClass(CLILogger)


def get_logger(name: str) -> CLILogger:
    """Type safety wrapper for the `logging.getLogger` function."""
    logger = logging.getLogger(name)
    assert isinstance(logger, CLILogger)
    return logger
