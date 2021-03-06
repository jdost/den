"""Den lifespan commands

These are all of the commands associated with the lifespan of a "den" container
from creation, starting, stopping, and deleting.  This expects the images that
are used to exist in the docker instance (or be able to be pulled down).

Config settings::
    [image]
    default=image_tag  # image tag in docker to create
    command=/shell/command  # command to execute in the container (should
        # probably be a shell)

    [ports]
    <CONTAINER_PORT>=<HOST_PORT>  # port forwards to make to localhost, where
        # 80=8080 would mean container:80 is reached from the localhost:8080
        # on the host system, if no host port is specified, it will be the same
        # port
"""
import logging
import os

from os.path import expanduser

import click

from .. import shell
from .. import utils

log = logging.getLogger(__name__)

DOCKER_CREATE_CMD = ("docker create --hostname {name} --interactive "
                     "--label den --name {name} --tty --volume "
                     "{cwd}:/src{extra_args} {image}")
DOCKER_START_CMD = "docker start --attach --interactive {name}"
DOCKER_STOP_CMD = "docker stop --time 1 {name}"
DOCKER_DELETE_CMD = "docker rm --force {name}"
HOME = expanduser("~")

__commands__ = ["create_den", "start_den", "stop_den", "delete_den",
                "list_dens"]


class UndefinedImageException(click.ClickException):
    """Exception raised when no image can be inferred.
    Images are defined either via a CLI argument or via the configuration
    files.
    """
    def __init__(self):
        click.ClickException.__init__(
            self, "There is no defined image to build off of.")


# > den create [OPTIONS] [<name>] [-- <cmd>]
@click.command("create", short_help="Create a new den")
@click.option("-s", "--start", is_flag=True, default=False,
              help="Start the den upon creation")
@click.option("-i", "--image", default=None, metavar="DOCKER_IMAGE",
              help="Image to build off of")
@click.option("--device", default=None, metavar="/dev/DEVICE",
              help="Devices to pass to container")
@click.option("--with-docker", is_flag=True, default=False,
              help="Mount docker daemon within container")
@click.option("--with-ssh", is_flag=True, default=False,
              help="Mount ssh agent within container")
@click.argument("name", required=False, default=None)  # Name for the den
@click.argument("cmd", nargs=-1)  # Command to run in container
@click.pass_obj
def create_den(context, start, image,  # pylint: disable=too-many-arguments
               with_docker, with_ssh, name, cmd, device):
    """Creates the development den

    This is a reusable container created based on the argument and configured
    definition.  By default it is not started (just created, so a
    `docker ps -a` will show the container, but it won't be running).
    """
    use_default = image is None
    if use_default:
        log.info("No image provided, using default")
    image = image if image else context.config.get("image", "default", False)
    if not image:
        log.warn("No default found in configuration files.")
        raise UndefinedImageException()

    name = name if name else context.config.get(
        "image", "name", context.default_name)
    cmd = cmd if cmd else context.config.get("image", "command")
    cwd = (context.cwd + "/") if not context.cwd.endswith("/") else context.cwd
    extra_args = [""]

    if isinstance(cmd, (tuple, list)):
        cmd = " ".join(cmd)

    if with_docker:
        extra_args.append("--volume "
                          "/var/run/docker.sock:/var/run/docker.sock")
        extra_args.append("--volume " +
                          HOME + "/.docker:/root/.docker")
    if with_ssh:
        ssh_agent = os.environ.get("SSH_AUTH_SOCK", None)
        if not ssh_agent:
            log.warn("No ssh agent to mount, skipping")
        else:
            extra_args.append("--volume " +
                              ssh_agent + ":/var/run/ssh_agent.sock")
            extra_args.append("--env "
                              "SSH_AUTH_SOCK=/var/run/ssh_agent.sock")
    if device:
        extra_args.append("--device " + device)

    for guest, host in context.config.get_section("ports").items():
        extra_args.append(
            "--publish {}:{}".format(guest, host) if host else str(guest))

    # NOTE: tried to do creation using the API but volume mounting didn't work
    cmd = " {}".format(cmd) if cmd else ""
    with log.report_success(
        "Creating den environment `{}` with `{}` base"
        .format(name, image if not use_default else "default"),
        debug=context.debug
    ):
        shell.run(DOCKER_CREATE_CMD.format(
            name=name, cwd=cwd, image=image,
            extra_args=" ".join(extra_args)) + cmd, quiet=shell.ALL)

    if start:
        start_den.callback(name)


# > den start [<name>]
@click.command("start", short_help="Start an existing den")
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_obj
def start_den(context, name):
    """Starts the specified development den
    """
    name = name if name else context.default_name
    log.echo("Starting `{}` environment...".format(name))
    shell.run(DOCKER_START_CMD.format(**locals()), interactive=True,
              suppress=True)


# > den stop [<name>]
@click.command("stop", short_help="Stop a running den")
@click.option("-d", "--delete", is_flag=True, default=False,
              help="Delete the den after stopping it")
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_obj
def stop_den(context, delete, name=None):
    """Stops the specified develoment den
    """
    if not isinstance(delete, bool):
        name = delete
        delete = False

    name = name if name else context.default_name
    with log.report_success("Spinning down `{}` environment".format(name),
                            debug=context.debug):
        shell.run(DOCKER_STOP_CMD.format(**locals()), quiet=shell.ALL)

    if delete:
        delete_den.callback([name])


# > den delete [<name>]
@click.command("delete", short_help="Delete an existing den")
@click.option("-a", "--all", is_flag=True, default=False,
              help="Delete all dens")
@click.argument("names", required=False, nargs=-1,
                default=None)  # Name for the den
@click.pass_obj
@utils.uses_docker
def delete_den(context, all, names):  # pylint: disable=redefined-builtin
    """Deletes the specified development den(s)

    Will attempt to delete the specified dens.
    """
    if all:
        den_filter = {"all": True, "filters": {"label": "den"}}
        names = [container.name for container
                 in context.docker.containers.list(**den_filter)]
        if names:
            click.confirm("This will delete the containers: "
                          "{}".format(", ".join(names)), abort=True)
    elif not names:
        names = [context.default_name]

    for name in names:
        with log.report_success(
            "Removing the `{}` environment".format(name),
            debug=context.debug, abort=False
        ):
            shell.run(DOCKER_DELETE_CMD.format(**locals()), quiet=shell.ALL)


# > den list
@click.command("list", short_help="List current dens")
@click.option("-r", "--running", is_flag=True, default=False,
              help="Only display running dens")
@click.pass_obj
@utils.uses_docker
def list_dens(context, running):
    """List the existing den containers

    Filters based on the metadata label applied and gives a simple summary of
    the state of containers running.
    """
    kwargs = {
        "all": not running,
        "filters": {"label": "den"}
    }
    output = [["NAME", "STATUS", "IMAGE"]]
    containers = context.docker.containers.list(**kwargs)
    log.info("Found %d containers.", len(containers))

    for container in containers:
        log.debug("`%s` has tags `%s`",
                  container.name, ",".join(container.image.tags))
        tag = container.image.tags[0] if container.image.tags \
            else container.image.short_id
        output.append([container.name, container.status, tag])

    log.echo("\n".join(utils.align_table(output, min_length=8)))
