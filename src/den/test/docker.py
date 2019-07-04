handlers = {}


def define_handler(name):
    def decorator(func):
        handlers[name] = func
        return func

    return decorator


class DictObject(object):
    def __init__(self, **props):
        for k, v in props.items():
            if isinstance(v, dict):
                setattr(self, k, DictObject(**v))
            else:
                setattr(self, k, v)


@define_handler("docker.containers.list")
def _fix_container(*containers):
    if isinstance(containers[0], list):
        return _fix_container(*containers[0])

    return [DictObject(**container) for container in containers]


class TestDocker(object):
    def __init__(self, name, *arg, **values):
        self.name = name
        if arg:
            self._value = arg[0]

        self._values = values

    def __call__(self, *args, **kwargs):
        value = self.__dict__.get("_value", None)
        if self.name in handlers:
            return handlers[self.name](value)

        return value

    def __getattr__(self, name):
        if name in self.__dict__:
            return getattr(self.__dict__, name)

        val = self._values.get(name, {})
        full_name = ".".join([self.name, name])
        return (
            TestDocker(full_name, **val)
            if isinstance(val, dict)
            else TestDocker(full_name, val)
        )
