from typing import Any, Dict, List, Optional

class Image:
    short_id: str
    tags: List[str]

class Container:
    image: Image
    name: str
    status: str

class ContainerCollection:
    def list(
        self,
        all: bool = ...,
        before: Optional[str] = ...,
        filters: Optional[Dict[str, Any]] = ...,
        limit: int = ...,
        since: Optional[str] = ...,
        sparse: bool = ...,
        ignore_removed: bool = ...,
    ) -> List[Container]: ...

class DockerClient:
    containers: ContainerCollection

def from_env() -> DockerClient: ...
