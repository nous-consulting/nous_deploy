import os

from nous_deploy.services import run_as_user
from nous_deploy.services import Service
from nous_deploy.services import run_as_sudo

from fabric.contrib.files import exists
from fabric.context_managers import cd
from fabric.operations import open_shell
from fabric.operations import run


class Sentry(Service):

    @property
    def service_path(self):
        return os.path.join("/srv", self.name)

    @property
    def python_path(self):
        return os.path.join(self.service_path, 'python')

    @property
    def data_path(self):
        return os.path.join(self.service_path, 'data')

    @property
    def port(self):
        return self.settings.port

    @property
    def db_path(self):
        return os.path.join(self.data_path, 'sentry.db.sqlite')

    @property
    def url_prefix(self):
        return 'http://%s' % self.settings['hostname']

    @property
    def config_file(self):
        return os.path.join(self.service_path, 'sentry.conf.py')

    @property
    def sentry_bin(self):
        return os.path.join(self.python_path, 'bin/sentry')

    @property
    def password_salt(self):
        return '853dswA4'

    @property
    def password_hexdigest(self):
        from hashlib import sha1
        return sha1(self.password_salt + self.settings['admin_password']).hexdigest()

    def sentry(self, command):
        run('%s --config=%s %s' % (self.sentry_bin, self.config_file, command))

    @run_as_user
    def init_database(self):
        self.upload_config_template('initial_data.json',
                                    os.path.join(self.data_path, 'initial_data.json'),
                                    {'service': self})

        self.sentry('upgrade --noinput')
        # Make sure initial.json is deleted so it doesn't get loaded
        # on next `sentry syncdb`
        run('rm %s' % os.path.join(self.data_path, 'initial_data.json'))

    @run_as_sudo
    def setup(self):
        self.server.ensure_user(self.user)
        run('mkdir -p %s' % (self.service_path,))
        run('chown -R %s:%s %s' % (self.user, self.user, self.service_path))
        run('virtualenv --no-site-packages %s' % self.python_path)
        run('%s install sentry' % (os.path.join(self.python_path, 'bin/pip')))
        self.configure()
        self.init_database()

    @run_as_sudo
    def prepare(self):
        packages = ['python-virtualenv', 'python-dev', 'supervisor']
        for package in packages:
            self.server.apt_get_install(package)


    @run_as_sudo
    def configure_supervisor(self):
        self.upload_config_template('sentry_supervisord.conf',
                                    '/etc/supervisor/conf.d/%s.conf' % self.name,
                                    {'service': self})
    @run_as_user
    def configure(self):
        run('mkdir -p %s' % self.data_path)
        self.upload_config_template('sentry.conf.py',
                                    self.config_file,
                                    {'service': self})
        self.configure_supervisor()

    @run_as_sudo
    def start(self):
        run('supervisorctl start %s' % self.name)

    @run_as_sudo
    def stop(self):
        run('supervisorctl stop %s' % self.name)

    @run_as_sudo
    def restart(self):
        run('supervisorctl restart %s' % self.name)

    @run_as_sudo
    def remove(self):
        self.stop()
        run('rm -rf %s' % self.service_path)
        run('rm -f /etc/supervisor/conf.d/%s.conf' % self.name)
