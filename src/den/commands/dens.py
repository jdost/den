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
import click
import os

from docker.types import Mount
from datetime import datetime

from .. import shell
from .. import utils


DOCKER_CREATE_CMD = ("docker create --hostname {name} --interactive "
    "--label den --name {name} --tty --volume {cwd}:/src {image}")
DOCKER_START_CMD = "docker start --attach --interactive {name}"
DOCKER_STOP_CMD = "docker stop --time 1 {name}"
DOCKER_DELETE_CMD = "docker rm --force {name}"

__commands__ = ["create_den", "start_den", "stop_den", "delete_den",
                "list_dens"]


class UndefinedImageException(click.ClickException):
    def __init__(self):
        click.ClickException.__init__(
            self, "There is no defined image to build off of.")


# > den create [OPTIONS] [<name>] [-- <cmd>]
@click.command("create", short_help="Create a new den")
@click.option("-s", "--start", is_flag=True, default=False,
              help="Start the den upon creation")
@click.option("-i", "--image", default=None, help="Image to build off of")
@click.argument("name", required=False, default=None)  # Name for the den
@click.argument("cmd", nargs=-1)  # Command to run in container
@click.pass_obj
def create_den(context, start, image, name, cmd):
    """Creates the development den

    This is a reusable container created based on the argument and configured
    definition.  By default it is not started (just created, so a
    `docker ps -a` will show the container, but it won't be running).
    """
    use_default = image != None
    image = image if image else context.config.get("image", "default", False)
    if not image:
        raise UndefinedImageException()

    name = name if name else context.default_name
    cmd = cmd if cmd else context.config.get("image", "command")
    cwd = (context.cwd + "/") if not context.cwd.endswith("/") else context.cwd

    ports = []
    for guest, host in context.config.get_section("ports").iteritems():
        ports.append("{}:{}".format(guest, host) if host else str(guest))
    ports = ",".join(ports)

    # NOTE: tried to do creation using the API but volume mounting didn't work
    cmd = " {}".format(cmd) if cmd else ""
    with utils.report_success("Creating den environment with {} base".format(
        image if use_default else "default")):
        shell.run(DOCKER_CREATE_CMD.format(**locals()) + cmd, quiet=shell.ALL)

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
    click.echo("Starting `{}` environment...".format(name))
    shell.run(DOCKER_START_CMD.format(**locals()), interactive=True,
              suppress=True)


# > den stop [<name>]
@click.command("stop", short_help="Stop a running den")
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_obj
def stop_den(context, name):
    """Stops the specified develoment den
    """
    name = name if name else context.default_name
    with utils.report_success("Spinning down `{}` environment".format(name)):
        shell.run(DOCKER_STOP_CMD.format(**locals()), quiet=shell.ALL)


# > den delete [<name>]
@click.command("delete", short_help="Delete an existing den")
@click.option("-a", "--all", is_flag=True, default=False,
              help="Delete all dens")
@click.argument("names", required=False, nargs=-1, default=None)  # Name for the den
@click.pass_obj
def delete_den(context, all, names):
    """Deletes the specified development den(s)

    Will attempt to delete the specified dens.
    """
    if all:
        den_filter = {"all": True, "filters": {"label": "den"}}
        names = [container.name for container
                 in context.docker.containers.list(**den_filter)]
        if len(names):
            click.confirm("This will delete the containers: "
                          "{}".format(", ".join(names)), abort=True)
    elif not names:
        names = [context.default_name]

    for name in names:
        with utils.report_success("Removing the `{}` environment".format(name),
                abort=False):
            shell.run(DOCKER_DELETE_CMD.format(**locals()), quiet=shell.ALL)


# > den list
@click.command("list", short_help="List current dens")
@click.option("-r", "--running", is_flag=True, default=False,
              help="Only display running dens")
@click.pass_obj
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
    for container in context.docker.containers.list(**kwargs):
        tag = container.image.tags[0] if len(container.image.tags) \
                else container.image.short_id
        output.append([container.name, container.status, tag])

    click.echo("\n".join(utils.align_table(output, min_length=8)))
