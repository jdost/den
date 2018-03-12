import functools

from .test_base import TestCase, ConfigurationError


def with_config(**values):
    def decorator(func):
        @functools.wraps(func)
        def decorated_func(self, *args, **kwargs):
            with self.with_config(**values):
                return func(self, *args, **kwargs)

        return decorated_func

    return decorator


def expose(func):
    @functools.wraps(func)
    def decorated_func(self, *args, **kwargs):
        with self.debug():
            return func(self, *args, **kwargs)

    return decorated_func
