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
from typing import Mapping, Optional, Sequence

import click

from den import log, shell, utils
from den.context import Context

logger = log.get_logger(__name__)
DOCKER_CREATE_CMD = (
    "docker create --hostname {name} --interactive "
    "--label den --name {name} {ports}--tty --volume "
    "{cwd}:/src{extra_args} {image}"
)
DOCKER_START_CMD = "docker start --attach --interactive {name}"
DOCKER_STOP_CMD = "docker stop --time 1 {name}"
DOCKER_DELETE_CMD = "docker rm --force {name}"

__commands__ = [
    "create_den",
    "start_den",
    "stop_den",
    "delete_den",
    "list_dens",
]


class UndefinedImageException(click.ClickException):
    """Exception raised when no image can be inferred.
    Images are defined either via a CLI argument or via the configuration
    files.
    """

    def __init__(self) -> None:
        click.ClickException.__init__(
            self, "There is no defined image to build off of."
        )


# > den create [OPTIONS] [<name>] [-- <cmd>]
@click.command("create", short_help="Create a new den")
@click.option(
    "-s",
    "--start",
    is_flag=True,
    default=False,
    help="Start the den upon creation",
)
@click.option("-i", "--image", default=None, help="Image to build off of")
@click.option(
    "--with-docker",
    is_flag=True,
    default=False,
    help="Mount docker daemon within container",
)
@click.argument("name", required=False, default=None)  # Name for the den
@click.argument("cmd", nargs=-1)  # Command to run in container
@click.pass_context
def create_den(  # pylint: disable=too-many-arguments
    ctx: click.Context,
    start: bool,
    image: str,
    with_docker: bool,
    name: str,
    cmd: Sequence[str],
) -> None:
    """Creates the development den

    This is a reusable container created based on the argument and configured
    definition.  By default it is not started (just created, so a
    `docker ps -a` will show the container, but it won't be running).
    """
    context = ctx.obj
    use_default = image is None
    if use_default:
        logger.info("No image provided, using default")
    image = image if image else context.config.get("image", "default", False)
    if not image:
        logger.warning("No default found in configuration files.")
        raise UndefinedImageException()

    name = (
        name
        if name
        else context.config.get("image", "name", context.default_name)
    )
    cmd = cmd if cmd else context.config.get("image", "command")
    cwd = (context.cwd + "/") if not context.cwd.endswith("/") else context.cwd
    extra_args = [""]

    if isinstance(cmd, tuple):
        cmd = " ".join(cmd)

    if with_docker:
        extra_args.append("--volume")
        extra_args.append("/var/run/docker.sock:/var/run/docker.sock")

    ports = []
    for guest, host in context.config.get_section("ports").items():
        ports.append(
            "--publish {}:{}".format(guest, host) if host else str(guest)
        )

    # NOTE: tried to do creation using the API but volume mounting didn't work
    cmd = " {}".format(cmd) if cmd else ""
    with logger.report_success(
        "Creating den environment `{}` with `{}` base".format(
            name, image if not use_default else "default"
        )
    ):
        shell.run(
            DOCKER_CREATE_CMD.format(
                name=name,
                ports=" ".join(ports) + " " if ports else "",
                cwd=cwd,
                image=image,
                extra_args=" ".join(extra_args),
            )
            + cmd,
            quiet=shell.ALL,
        )

    if start:
        ctx.invoke(start_den, name=name)


# > den start [<name>]
@click.command("start", short_help="Start an existing den")
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_obj
def start_den(context: Context, name: Optional[str]) -> None:
    """Starts the specified development den
    """
    name = name if name else context.default_name
    logger.echo("Starting `%s` environment...", name)
    shell.run(
        DOCKER_START_CMD.format(**locals()), interactive=True, suppress=True
    )


# > den stop [<name>]
@click.command("stop", short_help="Stop a running den")
@click.option(
    "-d",
    "--delete",
    is_flag=True,
    default=False,
    help="Delete the den after stopping it",
)
@click.argument("name", required=False, default=None)  # Name for the den
@click.pass_context
def stop_den(
    ctx: click.Context, delete: bool, name: Optional[str] = None
) -> None:
    """Stops the specified develoment den
    """
    context = ctx.obj
    if not isinstance(delete, bool):
        name = delete
        delete = False

    name = name if name else context.default_name
    with logger.report_success("Spinning down `{}` environment".format(name)):
        shell.run(DOCKER_STOP_CMD.format(**locals()), quiet=shell.ALL)

    if delete:
        ctx.invoke(delete_den, [name])


# > den delete [<name>]
@click.command("delete", short_help="Delete an existing den")
@click.option(
    "-a", "--all", is_flag=True, default=False, help="Delete all dens"
)
@click.argument(
    "names", required=False, nargs=-1, default=None
)  # Name for the den
@click.pass_obj
@utils.uses_docker
def delete_den(
    context: Context,
    all: bool,  # pylint: disable=redefined-builtin
    names: Sequence[str],
) -> None:
    """Deletes the specified development den(s)

    Will attempt to delete the specified dens.
    """
    if all:
        den_filter: Mapping[str, object] = {
            "all": True,
            "filters": {"label": "den"},
        }
        names = [
            container.name
            for container in context.docker.containers.list(**den_filter)
        ]
        if names:
            click.confirm(
                "This will delete the containers: "
                "{}".format(", ".join(names)),
                abort=True,
            )
    elif not names:
        names = [context.default_name]

    for name in names:
        with logger.report_success(
            "Removing the `{}` environment".format(name)
        ):
            shell.run(DOCKER_DELETE_CMD.format(**locals()), quiet=shell.ALL)


# > den list
@click.command("list", short_help="List current dens")
@click.option(
    "-r",
    "--running",
    is_flag=True,
    default=False,
    help="Only display running dens",
)
@click.pass_obj
@utils.uses_docker
def list_dens(context: Context, running: bool) -> None:
    """List the existing den containers

    Filters based on the metadata label applied and gives a simple summary of
    the state of containers running.
    """
    kwargs: Mapping[str, object] = {
        "all": not running,
        "filters": {"label": "den"},
    }
    output = [["NAME", "STATUS", "IMAGE"]]
    containers = context.docker.containers.list(**kwargs)
    logger.info("Found %i containers.", len(containers))

    for container in containers:
        logger.debug(
            "`%s` has tags `%s`", container.name, ",".join(container.image.tags)
        )
        tag = (
            container.image.tags[0]
            if container.image.tags
            else container.image.short_id
        )
        output.append([container.name, container.status, tag])

    logger.echo("\n".join(utils.align_table(output, min_length=8)))
