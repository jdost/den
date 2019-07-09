"""Utility function collection

Collection of random helper functions that are designed to be simple and
shareable for.  Basically a cop-out in scope definition but also kind of the
catchall for misc helpers.
"""
import functools
import importlib
import os
import os.path
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Sequence,
    TypeVar,
    Union,
    cast,
)

import click

HOME = os.path.expanduser("~")
FuncT = TypeVar("FuncT", bound=Callable[..., object])
_T = TypeVar("_T")


def align_table(
    table_data: Sequence[Any],
    max_length: int = 99999,
    min_length: int = 1,
    seperator: str = " ",
) -> Generator[str, None, None]:
    """Align columnar data for output

    Takes a 2 dimensional set of data consisting of rows of columns and formats
    each row to align in columns with each other.  Relies on the built in
    string formatting system to generate each line.  The `max_length` argument
    allows for limiting how wide a column can be.

    NOTE: Uses the first row as an indicator of column number, if any rows are
    of different size, they will either error (if shorter) or truncate (if
    longer).
    """
    format_str = ""
    for column in range(len(table_data[0])):
        width = max(min_length, *[len(row[column]) for row in table_data])
        format_str += "{:" + str(min(max_length, width)) + "}" + seperator

    for row in table_data:
        yield format_str.format(*row)


def base_dir(*matches: str) -> Union[str, Path]:
    """Climb the file system until finding one of the matching indicators

    These indicators are files to look in the directory to indicate that it is
    the base directory to work out.  Example using `.git` will find the base
    directory of a git repositor.
    """
    directory = os.getcwd()
    while not any([os.path.exists(str(m)) for m in matches or [".git"]]):
        os.chdir("..")
        if os.getcwd() == "/" or os.getcwd() == HOME:
            os.chdir(directory)
            break

    value = os.getcwd()

    return value


def bind_module(module_name: str, parent_cmd: click.Group) -> None:
    """Binds commands to a parent subcommand from a module

    This is currently a work in progress on module discovery, this will
    probably be replaced with some annotation metadata system to better infer
    desired handling of members of a module rather than just inferring based on
    their class type.
    """
    module = importlib.import_module(module_name, __name__)
    if hasattr(module, "__commands__"):
        targets = getattr(module, "__commands__")
    else:
        targets = dir(module)

    for member_name in targets:
        member = getattr(module, member_name)
        if isinstance(member, click.Command):
            parent_cmd.add_command(member)


def cached_property(func: Callable[..., Any]) -> Any:
    """Property decorator that creates a cached/memoized member variable

    Like the `@property` decorator but only determines the value once and then
    caches it in a `_` prefixed member variable.
    """
    cached_name = "_" + func.__name__

    def cached_caller(self: object) -> Any:
        """decorated function"""
        if not hasattr(self, cached_name):
            setattr(self, cached_name, func(self))

        return getattr(self, cached_name)

    return property(cached_caller)


def dict_merge(*srcs: Dict[str, object], **kwargs: object) -> Dict[str, object]:
    """Merge multiple dictionaries together
    Takes a set of dictionaries (and addition key value pairs) and merges into
    a new dictionary.  This attempts to keep the passed in dictionaries
    immutable (so the values shouldn't change in them).

    If you use the `_deep` keyword, any values that are dictionaries will be
    merged rather than overwritten.
    """
    merged_dict: Dict[str, object] = {}
    deep = kwargs.get("_deep", False)

    def deep_merge(key: str, value: object) -> None:
        """Recursive merging check
        This will deep merge dictionary values, otherwise it will overwrite
        """
        if isinstance(value, dict):
            root = merged_dict.get(key, {})
            assert isinstance(root, dict)
            merged_dict[key] = dict_merge(root, value, _deep=deep)
        else:
            merged_dict[key] = value

    if "_deep" in kwargs:  # don't merge the special keyword
        del kwargs["_deep"]

    for src in list(srcs) + [kwargs]:  # toss kwargs on end
        if isinstance(src, dict):
            if deep:  # loop through k-v pairs if deep merging
                for key, val in src.items():
                    deep_merge(key, val)
            else:
                merged_dict.update(src)

    return merged_dict


class DockerConnectionException(click.ClickException):
    """Exception raised when an exception from docker is called, this is meant
    to be caught when docker is not running and present a clean error about
    this.
    """

    def __init__(self, cause: str) -> None:
        msg = (
            "{}, ensure that docker is running and that you have "
            "permissions to talk to it."
        ).format(cause)
        click.ClickException.__init__(self, msg)


def uses_docker(func: FuncT) -> FuncT:
    """Docker execution decorator

    Wraps the function/command to capture raised errors when trying to
    communicate using the Docker API in case it times out or has an error,
    meant to capture possible configuration errors or connection problems
    and cleanly report it up to the user.
    """
    from requests.exceptions import ConnectionError as RequestsConnectionError
    from den import log

    logger = log.get_logger(__name__)

    @functools.wraps(func)
    def capture_function(*args: Any, **kwargs: Any) -> Any:
        """Decorated wrapper around capturing docker related errors and raising
        a clean error for output.
        """
        debug = False
        if args and hasattr(args[0], "debug"):
            debug = args[0].debug

        try:
            return func(*args, **kwargs)
        except RequestsConnectionError:
            logger.error("Docker connection failed.")
            if debug:
                raise
            raise DockerConnectionException("Failed to connect to the daemon")

    return cast(FuncT, capture_function)
