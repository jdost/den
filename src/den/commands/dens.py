"""Den lifespan commands

These are all of the commands associated with the lifespan of a "den" container
from creation, starting, stopping, and deleting.  This expects the images that
are used to exist in the docker instance (or be able to be pulled down).
"""
import click
import os
import os.path
import sys
from docker.types import Mount
from .. import shell
from .. import utils

from datetime import datetime

DOCKER_CREATE_CMD = ("docker create --hostname {name} --interactive "
    "--label den --name {name} --tty --volume {cwd}:/src {image}")
DOCKER_START_CMD = "docker start --attach --interactive {name}"
DOCKER_STOP_CMD = "docker stop --time 1 {name}"
DOCKER_DELETE_CMD = "docker rm --force {name}"

def _start_container(name):
    click.echo("Starting `{}` environment...".format(name))
    shell.run(DOCKER_START_CMD.format(**locals()), interactive=True,
              suppress=True)


# > den create [OPTIONS] [<name>] [-- <cmd>]
@click.command("create")
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
        print("There is no defined image to build off of.")
        sys.exit(1)

    name = name if name else os.path.basename(context.cwd)
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
        _start_container(name)


# > den start [<name>]
@click.command("start")
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_obj
def start_den(context, name):
    """Starts the specified development den
    """
    name = name if name else os.path.basename(context.cwd)
    _start_container(name)


# > den stop [<name>]
@click.command("stop")
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_obj
def stop_den(context, name):
    """Stops the specified develoment den
    """
    name = name if name else os.path.basename(context.cwd)
    with utils.report_success("Spinning down `{}` environment".format(name)):
        shell.run(DOCKER_STOP_CMD.format(**locals()), quiet=shell.ALL)


# > den delete [<name>]
@click.command("delete")
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_obj
def delete_den(context, name):
    """Deletes the specified development den
    """
    name = name if name else os.path.basename(context.cwd)
    with utils.report_success("Removing the `{}` environment".format(name)):
        shell.run(DOCKER_DELETE_CMD.format(**locals()), quiet=shell.ALL)


# > den list
@click.command("list")
@click.option("-r", "--running", is_flag=True, default=False,
              help="Only display running dens")
@click.pass_obj
def list_dens(context, running):
    """List the existing den containers
    """
    kwargs = {
        "all": not running,
        "filters": {"label": "den"}
    }
    output = [["NAME", "STATUS", "IMAGE"]]
    for container in context.docker.containers.list(**kwargs):
        output.append([container.name, container.status, container.image.tags[0]])

    print("\n".join(utils.align_table(output, min_length=8)))
