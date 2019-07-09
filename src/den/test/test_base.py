""" Test utilities, these are included mocked constructs to aid in
writing tests against the internals of the utility.
"""
import unittest
from contextlib import contextmanager
from copy import copy
from io import StringIO
from types import ModuleType
from typing import Any, Callable, Dict, Generator, Optional, TypeVar, cast

import click
from click.testing import CliRunner, Result

from den.test.context import TestConfig, TestContext
from den.test.docker import TestDocker
from den.utils import cached_property, dict_merge

FuncT = TypeVar("FuncT", bound=Callable[..., object])
_T = TypeVar("_T")


class ConfigurationError(Exception):
    """Exception raised when the test runner is misconfigured."""


class Invoker:  # pylint: disable=too-few-public-methods
    """Scaffolded false Invoking class."""


class TestCase(unittest.TestCase):
    """Superset of the unittest TestCase for testing den
    Provides a standardized setup and access methods to simplify test writing
    against den.
    """

    command_base: Optional[ModuleType] = None
    config: Dict[str, Any] = {}
    docker: Optional[Dict[str, object]] = None
    _debug: bool = False

    def setUp(self) -> None:
        self.runner = CliRunner()
        self.context = TestContext()

    def tearDown(self) -> None:
        pass

    @cached_property
    def invoke(self) -> Invoker:
        """Call a command on the base command invocation

        Takes the declared based command set and provides invokable calls to
        the commands for testing.  This is a lazy declaration, so it will only
        create the wrapper on demand (and caches the created wrapper).  Usage::
            > self.invoke.den("create -s -i test test")
        """

        def wrapper(method: click.Command) -> FuncT:
            """Calling wrapper, builds a false invocation handler to an
            underlying click command for testing, this doesn't require or use
            the full click system, just short circuits to the invocation.
            """

            def caller(
                args: Optional[str] = None,
                stdin: Optional[StringIO] = None,
                assrt: bool = True,
                ctch: bool = False,
            ) -> Result:
                """Wrapped click executor of the target click command handler.
                """
                ctch = self._debug if ctch is None else ctch
                context = copy(self.context)
                context.config = TestConfig(**self.config)
                if self.docker is not None:
                    context.docker = TestDocker("docker", **self.docker)

                result = self.runner.invoke(
                    method,
                    args.split(" ") if args else [],
                    input=stdin,
                    catch_exceptions=ctch,
                    obj=context,
                )
                if assrt:
                    self.assertEqual(
                        result.exit_code,
                        0,
                        "Command {!s}:{} failed: {}".format(
                            method.name, args, result.output
                        ),
                    )
                return result

            return cast(FuncT, caller)

        if not self.command_base:
            raise ConfigurationError(
                "An invoking test needs a base command to invoke against."
            )

        invoker = Invoker()
        cmd: str
        for cmd in getattr(self.command_base, "__commands__"):
            wrapped_command: click.Command = wrapper(
                getattr(self.command_base, cmd)
            )
            setattr(invoker, cmd, wrapped_command)

        return invoker

    def assertOutput(self, left: str, right: str) -> None:
        self.assertEqual(left.strip(), right.strip())

    @contextmanager
    def with_config(
        self, _blank: bool = False, **values: Any
    ) -> Generator[None, None, None]:
        _original_config = self.config
        self.config = (
            values if _blank else dict_merge(self.config, values, _deep=True)
        )
        yield
        self.config = _original_config

    @contextmanager
    def with_debug(self) -> Generator[None, None, None]:
        __debug_orig = self._debug
        self._debug = True
        yield
        self._debug = __debug_orig
