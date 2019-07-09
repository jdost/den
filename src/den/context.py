"""Definition of the shared context extension provided to click
This is the object that is passed in via the `pass_obj` decorator and is
meant to combine and share runtime state in a standardized way.
"""
import os
from pathlib import Path
from typing import Optional, Union

import docker as _docker

from den import CONFIG_FILES, utils
from den.config import Config


class Context:
    """Cached context collector for commands

    Meant to provide lazy definitions for various contextually shared objects
    that commands will want without the specifics of their instantiation or
    definition being distributed among the commands.
    """

    debug: bool = False
    target_config: Optional[str] = None

    @utils.cached_property
    def config(self) -> Config:  # pylint: disable=no-self-use
        """(cached property) Contextual configuration"""
        return Config(*CONFIG_FILES)

    @utils.cached_property
    def cwd(self) -> Union[str, Path]:  # pylint: disable=no-self-use
        """(cached property) Determined root directory"""
        return utils.base_dir(".git", ".den.ini")

    @utils.cached_property
    def docker(self) -> _docker.DockerClient:  # pylint: disable=no-self-use
        """(cached property) Docker client interface"""
        return _docker.from_env()

    @utils.cached_property
    def default_name(self) -> str:
        """(cached property) inferred project name"""
        default_name = os.path.basename(self.cwd)
        assert isinstance(default_name, str)
        return default_name
