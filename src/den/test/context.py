from typing import Dict, Optional

from den.test.docker import TestDocker


class NotConfiguredError(Exception):
    pass


class TestContext(object):
    default_name: str = "test"
    cwd: str = "/test"
    debug: bool = True
    config: "TestConfig"
    _docker: Optional[TestDocker] = None

    @property
    def docker(self) -> TestDocker:
        if self._docker is None:
            raise NotConfiguredError(
                "This test needs to define a `docker` " "state."
            )
        return self._docker

    @docker.setter
    def docker(self, val: TestDocker) -> None:
        self._docker = val


class TestConfig(object):
    def __init__(self, **values: Dict[str, str]) -> None:
        self._values = values

    def get(
        self, section: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        _section = self._values.get(section, None)
        if not _section:
            return default

        res = _section.get(key, default)
        assert isinstance(res, str) or res is None
        return res

    def get_section(self, section: str) -> Dict[str, str]:
        return self._values.get(section, {})
