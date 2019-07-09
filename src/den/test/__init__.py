"""Den test submodule, provides helper functions and decorators to ease
testing your den commands.
"""
import functools
from typing import Any, Callable, TypeVar, cast

from .test_base import ConfigurationError, TestCase

FuncT = TypeVar("FuncT", bound=Callable[..., object])


def with_config(**values: Any) -> Callable[[FuncT], FuncT]:
    """Test wrapper with configuration definitions.

    Provide key-value pairs for overriden configuration values for a wrapped
    test function.
    """

    def decorator(func: FuncT) -> FuncT:
        """Decorating with_config function"""

        @functools.wraps(func)
        def decorated_func(self: TestCase, *args: Any, **kwargs: Any) -> Any:
            """Decorated with_config function"""
            with self.with_config(**values):
                return func(self, *args, **kwargs)

        return cast(FuncT, decorated_func)

    return decorator


def expose(func: FuncT) -> FuncT:
    """Test wrapper to expose debug output.

    Wraps a test function with a flag to enable debug output, used for better
    introspection into the internals of what is failing.
    """

    @functools.wraps(func)
    def decorated_func(self: TestCase, *args: Any, **kwargs: Any) -> Any:
        """Decorated expose function."""
        with self.with_debug():
            return func(self, *args, **kwargs)

    return cast(FuncT, decorated_func)
