from nous_deploy.services import Service
from nous_deploy.services import run_as_sudo

from fabric.operations import run, sudo


class Jenkins(Service):

    @run_as_sudo
    def setup(self):
        self.server.apt_get_install("jenkins")
        sudo("curl -L http://updates.jenkins-ci.org/update-center.json | sed '1d;$d' > /var/lib/jenkins/updates/default.json",
             user="jenkins")
        run('jenkins-cli -s http://localhost:8080 install-plugin git')
        run('jenkins-cli -s http://localhost:8080 install-plugin port-allocator')
        run('jenkins-cli -s http://localhost:8080 restart')
