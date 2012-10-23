import sys
import functools


def command(fn):
    parent = sys._getframe(1)
    commands = parent.f_locals.setdefault('_commands', [])
    commands.append(fn.__name__)
    def wrapper(self):
        print "Wrap wrap"
        return fn(self)
    return functools.wraps(fn)(wrapper)


class Server(object):

    def __init__(self, host, name, services, settings={}):
        self.host = host
        self.name = name
        self.services = [service.bind(self) for service in services]
        self.settings = settings

    @property
    def commands(self):
        return dict([(cmd, getattr(self, cmd))
                     for cmd in self._commands])

    @command
    def setup(self):
        print "Setting up", self.name


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

    @command
    def start(self):
        print "Starting", self.name, self.server.host

    @command
    def restart(self):
        print "Restarting", self.name, self.server.host


class Ututi(Service):

    @command
    def start(self):
        print "Starting", self.name, self.server.host

    @command
    def restart(self):
        print "Restarting", self.name, self.server.host


class BusyFlow(Service):

    @command
    def start(self):
        print "Starting", self.name, self.server.host

    @command
    def restart(self):
        print "Restarting", self.name, self.server.host


class BusyFlowCeleryWorker(Service):

    @command
    def start(self):
        print "Starting", self.name, self.server.host

    @command
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
