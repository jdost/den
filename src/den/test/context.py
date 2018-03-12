class NotConfiguredError(Exception):
    pass


class TestContext(object):
    default_name = "test"
    cwd = "/test"
    debug = True

    @property
    def docker(self):
        if not hasattr(self, "_docker"):
            raise NotConfiguredError("This test needs to define a `docker` "
                                     "state.")
        return self._docker


class TestConfig(object):
    def __init__(self, **values):
        self._values = values

    def get(self, section, key, default=None):
        _section = self._values.get(section, None)
        if not _section:
            return default

        return _section.get(key, default)

    def get_section(self, section):
        return self._values.get(section, {})
