import ConfigParser
import os.path
import utils


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

        for file in files:
            if not (file.startswith("/") or file.startswith("~")):
                if not base:
                    base = utils.base_dir(file)
                file = os.path.join(base, file)
            else:
                file = os.path.expanduser(file)

            if os.path.exists(file):
                self.parser.read(file)

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
