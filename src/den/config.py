"""Config interaction definition

Defines helpful wrappers around the `ConfigParser` system to obfuscate some of
the common patterns with interacting with variable system configurations and
resolution states.
"""
import ConfigParser
import os.path

import den.utils as utils


class Config(object):
    """ConfigParser wrapper

    Wraps the ConfigParser.ConfigParser class with some sane utility additions.
    These include default key values from missing config settings (instead of
    throwing an error) and existance checks when adding config files to be read
    from.
    """
    def __init__(self, *files):
        self.parser = ConfigParser.ConfigParser()
        base = None

        for f in files:
            if not (f.startswith("/") or f.startswith("~")):
                if not base:
                    base = utils.base_dir(f)
                f = os.path.join(base, f)
            else:
                f = os.path.expanduser(f)

            if os.path.exists(f):
                self.parser.read(f)

    def get(self, section, key, default=None):
        """Value lookup with default value

        Performs the section::key lookup in the config file hiearchy and will
        return the specified default value if there is no key defined.
        """
        try:
            return self.parser.get(section, key)
        except ConfigParser.NoSectionError:
            return default
        except ConfigParser.NoOptionError:
            return default

    def get_section(self, section):
        """Get dict of a section's key value pairs"""
        try:
            return dict(self.parser.items(section))
        except ConfigParser.NoSectionError:
            return {}
