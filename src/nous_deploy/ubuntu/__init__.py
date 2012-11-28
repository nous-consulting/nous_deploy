import os
import sys
import pkg_resources

from functools import wraps
from fabric.operations import sudo
from fabric.operations import run
from fabric.context_managers import cd
from fabric.contrib.files import append
from fabric.contrib.files import exists
from fabric.contrib.files import upload_template
from fabric.state import env
from fabric import network

from nous_deploy.services import host_string


def run_as(user):
    def decorator(func):
        @wraps(func)
        def inner(self, *args, **kwargs):
            env.server = self
            with host_string(network.join_host_strings(user, self.host, self.port)):
                return func(self, *args, **kwargs)
        inner._is_a_command = True
        return inner
    return decorator


def run_as_sudo(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        env.server = self
        return run_as(self.SUDO_USER)(func)(self, *args, **kwargs)
    wrapper._is_a_command = True
    return wrapper


class Server(object):

    SUDO_USER = 'root'
    port = 22

    def __init__(self, host, name, services, settings=None):
        self.collect_actions()
        self.host = host
        self.name = self.title = name
        self.services = [service.bind(self) for service in services]
        self.settings = settings if settings is not None else {}

    def collect_actions_from_class(self, cls):
        return [k for k, v in cls.__dict__.items()
                if hasattr(v, '_is_a_command')]

    def collect_actions(self):
        actions = set()
        for cls in reversed(self.__class__.__mro__):
            actions.update(self.collect_actions_from_class(cls))
        self._commands = list(actions)

    @property
    def commands(self):
        return dict([(cmd, getattr(self, cmd))
                     for cmd in self._commands])

    @run_as_sudo
    def apt_get_update(self, force=False):
        if not hasattr(env, '_APT_UPDATED') or force:
            run('apt-get update')
            env._APT_UPDATED = True

    @run_as_sudo
    def ssh_update_identities(self, username):
        home_dir = '/home/%s' % username
        if username == 'root':
            home_dir = '/root'

        with cd(home_dir):
            sudo('mkdir -p .ssh')
            identities = [ssh_key
                          for user, ssh_key in self.settings['identities']
                          if not user or user == username]
            append('.ssh/authorized_keys', identities, use_sudo=True)
            sudo('chown -R %s:%s .ssh' % (username, username))

    @run_as_sudo
    def ensure_user(self, username):
        username = username
        home_dir = '/home/%s' % username
        if not exists(home_dir):
            run('adduser %s --disabled-password --gecos ""' % username)
            self.ssh_update_identities(username)

    @run_as_sudo
    def apt_get_install(self, packages, options=''):
        """Installs package via apt get."""
        self.apt_get_update()
        run('apt-get install %s -y %s' % (options, packages,))

    def upload_config_template(self, name, to, context, template_dir=None,
                               **kwargs):
        if template_dir is None:
            template_dir = pkg_resources.resource_filename('nous_deploy', 'config_templates')
        self._upload_config_template(name, to, context, template_dir=template_dir,
                                     **kwargs)

    def _upload_config_template(self, name, to, context, template_dir,
                               use_jinja=True, backup=False, **kwargs):
        upload_template(name, to, context,
                        template_dir=template_dir,
                        use_jinja=use_jinja,
                        backup=backup,
                        **kwargs)

    @run_as_sudo
    def prepare(self):
        """Sets up all the dependencies"""
        for service in self.services:
            service.prepare()

    @run_as_sudo
    def setup(self):
        """Installs and sets up all the services themselves."""
        for service in self.services:
            service.setup()

    @run_as_sudo
    def configure(self):
        """Updates configuration for all the services."""
        for service in self.services:
            service.configure()

    @run_as_sudo
    def remove(self):
        """Stops and removes all the services."""
        for service in self.services:
            service.remove()
