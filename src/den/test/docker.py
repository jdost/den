from typing import Any, Callable, Dict, List, Optional, Union

HandlerT = Callable[..., object]
HANDLER: Dict[str, HandlerT] = {}


def define_handler(name: str) -> Callable[[HandlerT], HandlerT]:
    def decorator(func: HandlerT) -> HandlerT:
        HANDLER[name] = func
        return func

    return decorator


class DictObject(object):
    def __init__(self, **props: object) -> None:
        for k, v in props.items():
            if isinstance(v, dict):
                setattr(self, k, DictObject(**v))
            else:
                setattr(self, k, v)


@define_handler("docker.containers.list")
def _fix_container(
    *containers: Union[List[Dict[str, object]], Dict[str, object]]
) -> List[DictObject]:
    if isinstance(containers[0], list):
        return _fix_container(*containers[0])  # type: ignore

    fixed_containers: List[DictObject] = []
    for container in containers:
        assert isinstance(container, dict)
        fixed_containers.append(DictObject(**container))

    return fixed_containers


class TestDocker(object):
    def __init__(self, name: str, *arg: object, **values: object) -> None:
        self.name = name
        if arg:
            self._value = arg[0]

        self._values = values

    def __call__(self, *args: object, **kwargs: object) -> Any:
        value: Optional[object] = self.__dict__.get("_value", None)
        if self.name in HANDLER:
            return HANDLER[self.name](value)

        return value

    def __getattr__(self, name: str) -> Any:
        if name in self.__dict__:
            return getattr(self.__dict__, name)

        val = self._values.get(name, {})
        full_name = ".".join([self.name, name])
        return (
            TestDocker(full_name, **val)
            if isinstance(val, dict)
            else TestDocker(full_name, val)
        )
