import sys
from contextlib import contextmanager
from functools import wraps

from fabric.api import run
from fabric.state import env
from fabric import network
from fabric.context_managers import cd


@contextmanager
def host_string(new_host_string):
    try:
        old_host_string = env.host_string
        env.host_string = new_host_string
        yield
    finally:
        env.host_string = old_host_string


def run_as(user):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            old_user, host, port = network.normalize(env.host_string)
            with host_string(network.join_host_strings(user, host, port)):
                return func(*args, **kwargs)
        return inner
    return decorator


def run_as_sudo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_as(env.server.SUDO_USER)(func)(*args, **kwargs)
    return wrapper


def server_command(fn):
    parent = sys._getframe(1)
    commands = parent.f_locals.setdefault('_commands', [])
    commands.append(fn.__name__)
    def wrapper(self, *args, **kwargs):
        env.server = self
        with host_string(self.host):
            return fn(self, *args, **kwargs)
    return wraps(fn)(wrapper)


def service_command(fn):
    parent = sys._getframe(1)
    commands = parent.f_locals.setdefault('_commands', [])
    commands.append(fn.__name__)
    def wrapper(self, *args, **kwargs):
        env.service = self
        env.server = self.server
        with host_string(self.server.host):
            return fn(self, *args, **kwargs)
    return wraps(fn)(wrapper)


class Server(object):

    SUDO_USER = 'root'

    def __init__(self, host, name, services, settings={}):
        self.host = host
        self.name = name
        self.services = [service.bind(self) for service in services]
        self.settings = settings

    @property
    def commands(self):
        return dict([(cmd, getattr(self, cmd))
                     for cmd in self._commands])

    @server_command
    @run_as_sudo
    def apt_get_update(self, force=False):
        if not hasattr(env, '_APT_UPDATED') or force:
            run('apt-get update')
            env._APT_UPDATED = True

    @server_command
    @run_as_sudo
    def apt_get_install(self, packages, options=''):
        """Installs package via apt get."""
        self.apt_get_update()
        run('apt-get install %s -y %s' % (options, packages,))


class Service(object):

    def __init__(self, name, settings={}):
        self._name = name
        self.settings = settings
        self.server = None

    @property
    def commands(self):
        return dict([(cmd, getattr(self, cmd))
                     for cmd in self._commands])

    def bind(self, server):
        self.server = server
        return self

    @property
    def name(self):
        if self.server:
            return "{host}_{service}".format(host=self.server.name, service=self._name)
        return self._name


class Sentry(Service):

    @service_command
    def start(self):
        print "Starting", self.name, self.server.host

    @service_command
    def restart(self):
        print "Restarting", self.name, self.server.host


class Ututi(Service):

    @service_command
    @run_as('ututi')
    def staging_release(self):
        run('/srv/en.u2ti.com/instance/bin/release_latest.sh')

    @service_command
    @run_as('ututi')
    def prepare(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/prepare.sh')

    @service_command
    @run_as('ututi')
    def release(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/release_latest.sh')

    @service_command
    @run_as('ututi')
    def start(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/server_start.sh')

    @service_command
    @run_as('ututi')
    def stop(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/server_stop.sh')

    @service_command
    @run_as('ututi')
    def status(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/server_status.sh')

    @service_command
    @run_as('ututi')
    def restart(self):
        self.stop()
        self.start()


class BusyFlow(Service):

    @service_command
    def start(self):
        print "Starting", self.name, self.server.host

    @service_command
    def restart(self):
        print "Restarting", self.name, self.server.host


class BusyFlowCeleryWorker(Service):

    @service_command
    def start(self):
        print "Starting", self.name, self.server.host

    @service_command
    def restart(self):
        print "Restarting", self.name, self.server.host


def init(servers):
    scope = {}
    for server in servers:
        for command_name, cmd in server.commands.items():
            command_name = '{server}_{command}'.format(server=server.name,
                                                       command=command_name)
            scope[command_name] = cmd
        for service in server.services:
            for command_name, cmd in service.commands.items():
                command_name = '{service}_{command}'.format(service=service.name,
                                                            command=command_name)
                scope[command_name] = cmd
    return scope
