import unittest
from contextlib import contextmanager
from copy import copy
from typing import Any, Dict
from unittest.mock import patch

from click import MultiCommand
from click.testing import CliRunner

from den.utils import cached_property, dict_merge

from .context import TestConfig, TestContext
from .docker import TestDocker


class ConfigurationError(Exception):
    pass


class Invoker(object):
    pass


class TestCase(unittest.TestCase):
    command_base = None
    config: Dict[str, Any] = {}
    docker = None
    _debug = False

    def setUp(self):
        self.runner = CliRunner()
        self.context = TestContext()

    def tearDown(self):
        pass

    @cached_property
    def invoke(self):
        """Call a command on the base command invocation

        Takes the declared based command set and provides invokable calls to
        the commands for testing.  This is a lazy declaration, so it will only
        create the wrapper on demand (and caches the created wrapper).  Usage::
            > self.invoke.den("create -s -i test test")
        """

        def wrapper(method):
            def caller(args=None, stdin=None, assrt=True, ctch=None):
                ctch = self._debug if ctch is None else ctch
                context = copy(self.context)
                context.config = TestConfig(**self.config)
                if self.docker:
                    context._docker = TestDocker("docker", **self.docker)

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

            return caller

        if not self.command_base:
            raise ConfigurationError(
                "An invoking test needs a base command to " "invoke against."
            )

        invoker = Invoker()
        for cmd in getattr(self.command_base, "__commands__"):
            wrapped_command = wrapper(getattr(self.command_base, cmd))
            setattr(invoker, cmd, wrapped_command)

        return invoker

    def assertOutput(self, left, right):
        self.assertEqual(left.strip(), right.strip())

    @contextmanager
    def with_config(self, _blank=False, **values):
        _original_config = self.config
        self.config = (
            values if _blank else dict_merge(self.config, values, _deep=True)
        )
        yield
        self.config = _original_config

    @contextmanager
    def debug(self):
        __debug_orig = self._debug
        self._debug = True
        yield
        self._debug = __debug_orig
