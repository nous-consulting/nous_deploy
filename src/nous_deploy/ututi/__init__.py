from fabric.operations import run
from fabric.context_managers import cd

from nous_deploy.services import run_as
from nous_deploy.services import service_command
from nous_deploy.services import Ututi


class Ututi(Service):

    @service_command
    @run_as('ututi')
    def staging_release(self):
        run('/srv/en.u2ti.com/instance/bin/release_latest.sh')

    @service_command
    @run_as('ututi')
    def prepare(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/prepare_latest.sh')

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
