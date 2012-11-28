from nous_deploy.services import Service
from nous_deploy.services import run_as_sudo


class Git(Service):

    @run_as_sudo
    def setup(self):
        self.server.ensure_group('git')
        self.server.mkdir('/var/local/git')
