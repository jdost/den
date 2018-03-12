import den.test

from den.commands import dens
from den.utils import align_table
from mock import patch


class DensTest(den.test.TestCase):
    command_base = dens

    def setUp(self):
        den.test.TestCase.setUp(self)
        if self.command_base:
            self.shell_patch = patch(self.command_base.__name__ + ".shell.run")
            self.shell = self.shell_patch.start()

    def tearDown(self):
        if self.command_base:
            self.shell.stop()

    def assertExecuted(self, *cmds):
        self.shell.assert_called()

        for idx, cmd in enumerate(cmds):
            self.assertEquals(self.shell.call_args_list[idx][0], tuple([cmd]))

        self.shell.reset_mock()

class DenCreateTest(DensTest):
    config = {"image": {"default": "foo"}}
    def test_implied(self):
        """ `den create`
        Use implied defaults, this requires a default image be defined via the
        configs, otherwise it should fail.
        """
        self.invoke.create_den()
        self.assertExecuted("docker create --hostname {0} --interactive "
                "--label den --name {0} --tty --volume /test/:/src foo"\
                .format(self.context.default_name))

    def test_name(self):
        """ `den create <name>`
        Override the default naming of the created container.  This can be done
        via the CLI argument or via configuration.  In the case of both,
        precendence is to the CLI argument.
        """
        self.invoke.create_den("override")
        self.assertExecuted("docker create --hostname override --interactive "
                "--label den --name override --tty --volume /test/:/src foo")

        with self.with_config(image={"name": "configured"}):
            self.invoke.create_den()
            self.assertExecuted("docker create --hostname configured "
                    "--interactive --label den --name configured --tty "
                    "--volume /test/:/src foo")

        with self.with_config(image={"name": "configured"}):
            self.invoke.create_den("override")
            self.assertExecuted("docker create --hostname override "
                    "--interactive --label den --name override --tty "
                    "--volume /test/:/src foo")

    def test_command(self):
        """ `den create foo <command>`
        Override the executing command either via a CLI argument or a
        configuration value.  NOTE: the `test` is required, names have precedent
        over commands.
        """
        self.invoke.create_den("test /bin/echo")
        self.assertExecuted("docker create --hostname test --interactive "
                "--label den --name test --tty --volume /test/:/src foo "
                "/bin/echo")

        with self.with_config(image={"command": "/bin/foo"}):
            self.invoke.create_den("test", ctch=False)
            self.assertExecuted("docker create --hostname test --interactive "
                    "--label den --name test --tty --volume /test/:/src foo "
                    "/bin/foo")

        with self.with_config(image={"command": "/bin/foo"}):
            self.invoke.create_den("test /bin/echo")
            self.assertExecuted("docker create --hostname test --interactive "
                    "--label den --name test --tty --volume /test/:/src foo "
                    "/bin/echo")

    @den.test.with_config(ports={"9000": "9001", "80": "8080"})
    def test_ports(self):
        """ Configured port forwarding is honored
        If a port forwarding map is defined in the configuration, the created
        container should honor this port map in the creation.
        """
        self.invoke.create_den()
        self.assertExecuted("docker create --hostname {0} --interactive "
                "--label den --name {0} --publish 80:8080 --publish 9000:9001 "
                "--tty --volume /test/:/src foo"\
                    .format(self.context.default_name))

    @den.test.with_config(_blank=True)
    def test_unconfigured(self):
        """ Attempt commands with no configuration
        """
        result = self.invoke.create_den(assrt=False)
        self.assertEqual(result.exit_code, 1)

    def test_start(self):
        """ `den create --start`
        Should perform the normal creation but then also attempt to start the
        container.  This is a mixture of create and start.
        """
        self.invoke.create_den("--start")
        self.assertExecuted("docker create --hostname {0} --interactive "
                "--label den --name {0} --tty --volume /test/:/src foo"\
                .format(self.context.default_name), "docker start --attach "
                "--interactive {}".format(self.context.default_name))


class DenStartTest(DensTest):
    def test_basic(self):
        """ `den start`
        This does not do much beyond shell out to `docker start`.  This tests
        both an explicit declaration of the target den and the implied target.
        """
        self.invoke.start_den()  # implicitly start "test"
        self.assertExecuted("docker start --attach --interactive {}"\
                .format(self.context.default_name))  # the default_name is "test"

        self.invoke.start_den("explicit")  # explicitly start "foo"
        self.assertExecuted("docker start --attach --interactive explicit")


class DenStopTest(DensTest):
    def test_basic(self):
        """ `den stop`
        Stops the container, either by the default name or specified via a CLI
        argument.
        """
        self.invoke.stop_den()
        self.assertExecuted("docker stop --time 1 {}"\
                .format(self.context.default_name))

        self.invoke.stop_den("explicit")
        self.assertExecuted("docker stop --time 1 explicit")


class DenDeleteTest(DensTest):
    docker = {
        "containers": {
            "list": [{"name": "foo"}, {"name": "bar"}]
        }
    }

    def test_basic(self):
        """ `den delete`
        Deletes the container, either by the default name or specified via a
        CLI argument.
        """
        self.invoke.delete_den()
        self.assertExecuted("docker rm --force {}"\
                .format(self.context.default_name))

        self.invoke.delete_den("explicit")

        self.assertExecuted("docker rm --force explicit")

    def test_all(self):
        """ `den delete --all`
        Deletes *all* den created containers.
        """
        with patch("click.confirm") as confirmation:
            self.invoke.delete_den("--all")
            confirmation.assert_called_once()

        self.assertExecuted("docker rm --force foo", "docker rm --force bar")


class DenListTest(DensTest):
    docker = {
        "containers": {
            "list": [
                {"name": "foo", "status": "running",
                  "image": {"tags": ["image_foo"]}},
                {"name": "bar", "status": "ready",
                 "image": {"tags": [], "short_id": "image_bar"}}
            ]
        }
    }

    def test_basic(self):
        """ `den list`
        Outputs a cleaned up listing of all den containers.
        """
        result = self.invoke.list_dens()
        self.assertOutput(result.output,
            "\n".join(list(align_table([
                ["NAME", "STATUS", "IMAGE"],
                ["foo", "running", "image_foo"],
                ["bar", "ready", "image_bar"]
            ], min_length=8))))
