"""Config interaction definition

Defines helpful wrappers around the `ConfigParser` system to obfuscate some of
the common patterns with interacting with variable system configurations and
resolution states.
"""
import configparser
import os.path
from typing import Any, Dict, Optional

import den.utils as utils


class Config:
    """ConfigParser wrapper

    Wraps the configparser.ConfigParser class with some sane utility additions.
    These include default key values from missing config settings (instead of
    throwing an error) and existance checks when adding config files to be read
    from.
    """

    def __init__(self, *files: str) -> None:
        self.parser = configparser.ConfigParser()
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

    def get(self, section: str, key: str, default: Optional[Any] = None) -> Any:
        """Value lookup with default value

        Performs the section::key lookup in the config file hiearchy and will
        return the specified default value if there is no key defined.
        """
        try:
            return self.parser.get(section, key)
        except configparser.NoSectionError:
            return default
        except configparser.NoOptionError:
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get dict of a section's key value pairs"""
        try:
            return dict(self.parser.items(section))
        except configparser.NoSectionError:
            return {}
