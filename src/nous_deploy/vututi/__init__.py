from nous_deploy.services import Service, run_as
from nous_deploy.services import run_as_sudo
from fabric.api import run, sudo

def ensure_shm():
    # XXX check if file exists
    upload_config_template('S56mountshm.sh', '/etc/rcS.d/S56mounshm.sh',
                           use_sudo=True)
    run("chmod +x /etc/rcS.d/S56mounshm.sh")
    run("/etc/rcS.d/S56mounshm.sh")

# Refactor collectd into a service
def install_collectd():
    debian.apt_get_install("collectd git perl")
    with cd("/root/"):
        run("git clone https://github.com/joemiller/collectd-graphite.git")
        with cd("/root/collectd-graphite/"):
            run("perl Makefile.PL")
            run("make")
            run("make install")

def setup_collectd():
    upload_config_template('collectd.conf',
                           '/etc/collectd/collectd.conf',
                           use_sudo=True)
    run('/etc/init.d/collectd restart')


def compile_locales():
    run("locale-gen en_US.UTF-8")


def remove_apache_packages():
    run('apt-get remove -y apache2 apache2.2-common apache2.2-bin apache2-utils')


def install_postgresql_packages():
    run("add-apt-repository ppa:pitti/postgresql")
    debian.apt_get_update(force=True)
    debian.apt_get_install("postgresql-9.1")


@run_as_sudo
def nginx_install():
    debian.apt_get_install("nginx")
    run('rm -f /etc/nginx/sites-enabled/default')


@run_as_sudo
def nginx_setup():
    name = env.conf.SITE_NAME
    upload_config_template('nginx.config',
                           '/etc/nginx/sites-available/%s' % name, use_sudo=True)
    with settings(warn_only=True):
        run('ln -s /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s' % (name, name))
    run('/etc/init.d/nginx restart')


@run_as_sudo
def nginx_cleanup():
    name = env.conf.SITE_NAME
    run('rm /etc/nginx/sites-available/%s' % name)
    run('rm /etc/nginx/sites-enabled/%s' % name)
    run('/etc/init.d/nginx restart')


class VUtuti(Service):

    def install_common_software(self):

        common_packages = [
            'python-all-dbg',
            'libsane-dev',
            'libfreetype6-dev',
            'libjpeg62-dev',
            'zlib1g-dev',
            'liblcms1-dev',
            'build-essential',
            'python-all',
            'python-all-dev',
            'enscript',
            'libxslt1-dev',
            'libxml2-dev',
            'libpq-dev',
            'uuid-dev',
            'ccache',
            'python-software-properties',
            'swig']

        self.server.apt_get_install(" ".join(common_packages))

    @run_as_sudo
    def provision(self):
        ensure_shm()
        self.install_common_software()
        install_collectd()
        setup_collectd()
        compile_locales()

        install_postgresql_packages()
        remove_apache_packages()
        nginx_install()

    @run_as_sudo
    def setup_sandbox(self, pub_key_file=None):
        set_up_site_user(pub_key_file=pub_key_file)
        create_site_dirs()
        upload_release()
        build()

        with settings(instance='production'):
            create_instance()
            start_database()
            initialize_database()
            backup()
            start_server()

        with settings(instance='staging'):
            create_instance()
            start_database()
            import_backup()
            start_server()

        cron_setup()
        nginx_setup()


    @run_as_sudo
    @run_as('ututi')
    def staging_release(self):
        run('/srv/en.u2ti.com/instance/bin/release_latest.sh')

    @run_as_sudo
    @run_as('ututi')
    def prepare(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/prepare_latest.sh')

    @run_as_sudo
    @run_as('ututi')
    def release(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/release_latest.sh')

    @run_as_sudo
    @run_as('ututi')
    def start(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/server_start.sh')

    @run_as_sudo
    @run_as('ututi')
    def stop(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/server_stop.sh')

    @run_as_sudo
    @run_as('ututi')
    def status(self):
        with cd('/srv/ututi.com/instance'):
            run('bin/server_status.sh')

    @run_as_sudo
    @run_as('ututi')
    def restart(self):
        self.stop()
        self.start()

    def build(self, rebuild=False):
        code_dir = os.path.join(env.conf.SITE_DIR, 'code')
        build_lock = os.path.join(env.conf.SITE_DIR, 'code', 'build.lock')
        if exists(build_lock) and not rebuild:
            warn("Package is being built aborting!")
            return
        run("touch %s" % build_lock)
        try:
            package_file = get_last_packaged_release()
            release_name = os.path.basename(package_file).replace('.tar.gz', '')
            release_dir = os.path.join(env.conf.SITE_DIR, 'code', release_name)

            if exists(release_dir) and not rebuild:
                warn("Package has been built already run build:rebuild to rebuild it.")
                return

            if rebuild and exists(release_dir):
                run("rm -r %s" % release_dir)

            run("mkdir %s" % release_dir)
            run("tar -xvzf %s -C %s" % (package_file, code_dir))

            with cd(release_dir):
                with prefix("export PGPORT=%s" % env.conf.BUILD_DB_PORT):
                    run("""make BUILDOUT_OPTIONS="buildout:xapian-config=''" """)
                    try:
                        run("make start_database")
                        run("make test")
                    finally:
                        run("make stop_database")
                    run("make static")
                    run("rm -rf instance")
                    run("touch READY")
        finally:
            run("rm %s" % build_lock)
