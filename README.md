# DEN - Docker based Development Environment

Think of this as python's virtualenv but all in containers.  It is meant to give an
easy system for creating, spinning up, connecting to, and working within a custom
container based development environment.  It is just a wrapper around some docker
calls and easy setup for some built in features.

```
$ den create --start
Creating contained environment with default base...done
Starting `den-demo` environment...done
den-demo:/src $ ^C
$ den stop
Spinning down `den-demo` environment...done
```

### PWD mounting

When spun up, it will automatically mount the current working directory inside the
container.  This is so that you can continue to edit and modify the code in your
main OS and then compile/test/run the code inside of the container environment.

```
$ ls
README.md
$ den start
Starting `den-demo` environment...done
den-demo:/src $ ls
README.md
```

### Base Image Control

You can create and different base images to work out of and then dictate that when
creating the development environment.  This allows for you to set up things like a
favorite shell or common tools that you prefer using in the process once and then
dictate the image you want to use each time.

```
$ den create dev-python
Creating contained environment with dev-python base...done
```

### Repeatably create/spin up/spin down/delete environments

Helper actions are available for creating new environments with sane values for 
various options, starting and stopping them, and deleting them.  This is meant to
aid in rebuilding/nuking out bad containers and recreate.  (NOTE: because the local
folder is mounted (rather than copied) any changes made on it in the container will
persist outside of the lifespan of the container.)

```
$ den create --now
Creating contained environment with default base...done
Starting `den-demo` environment...done
den-demo:/src $ touch /root/test_file
den-demo:/src $ ls /root
test_file
den-demo:/src $ ^C
$ den stop
Spinning down `den-demo` environment...done
$ den start
Starting `den-demo` environment...done
den-demo:/src $ ls /root
test_file
```
