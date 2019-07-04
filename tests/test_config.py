import os
import tempfile

import den.test
from den.commands import config

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


class ConfigTest(den.test.TestCase):
    command_base = config

    def setUp(self):
        # create a temporary place to write to
        den.test.TestCase.setUp(self)
        self.context.cwd = tempfile.mkdtemp()
        self.context.target_config = self.context.cwd + "/.den.ini"

    def tearDown(self):
        # clean up the temporary target directory
        den.test.TestCase.tearDown(self)
        os.remove(self.context.target_config)
        os.rmdir(self.context.cwd)

    def assertValue(self, section, key, value):
        """Asserts the value of a lookup in the temporary config
        This is a helper around the temporary folder isolation of the
        filesystem calls inherent in this command test.
        """
        parser = ConfigParser()
        parser.read(self.context.target_config)
        self.assertEqual(parser.get(section, key), value)

    def test_new_set(self):
        """`den config set <section> <key> <value>`
        Basic, happy path declaration of a configuration value definition.
        """
        self.invoke.config_group("set foo bar baz")
        self.assertValue("foo", "bar", "baz")

    def test_overwrite(self):
        """`den config set <section> <key> <value>`
        Ensures that calling this subsequently does update the underlying
        configuration on the subsequent calls.
        """
        self.invoke.config_group("set foo bar baz")
        self.assertValue("foo", "bar", "baz")

        self.invoke.config_group("set foo bar buzz")
        self.assertValue("foo", "bar", "buzz")

    def test_combined_declaration(self):
        """`den config set <section>.<key> <value>`
        Allows for declaring a set using a dotted notation rather than separate
        arguments for section and key.
        """
        self.invoke.config_group("set foo.bar baz")
        self.assertValue("foo", "bar", "baz")

    def test_get(self):
        """`den config get <section> <key>`
        Basic config lookup, uses the `config set` command for defining the
        value.
        """
        self.invoke.config_group("set foo bar baz")
        result = self.invoke.config_group("get foo bar")
        self.assertOutput(result.output, "foo.bar = baz")

    def test_get_undefined(self):
        """`den config get <section> <key>`
        Checks failure scenario for a lookup of undefined values, both an
        undefined section and an undefined key in a defined section (meaning
        another key in that section exists).
        """
        result = self.invoke.config_group("get foo bar", assrt=False)
        self.assertEqual(result.exit_code, 1)
        self.assertOutput(result.output, "Error: No `foo` section defined.")

        self.invoke.config_group("set foo bar baz")
        result = self.invoke.config_group("get foo baz", assrt=False)
        self.assertEqual(result.exit_code, 1)
        self.assertOutput(result.output, "Error: No `foo.baz` option defined.")

    def test_get_combined(self):
        """`den config get <section>.<key>
        Ensures that the combined formation of `<section>.<key>` works along
        with the individual arguments format.
        """
        self.invoke.config_group("set foo bar baz")
        result = self.invoke.config_group("get foo.bar")
        self.assertOutput(result.output, "foo.bar = baz")
