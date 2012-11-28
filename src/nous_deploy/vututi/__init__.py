import os
import pkg_resources

from nous_deploy.services import Service, run_as
from nous_deploy.services import run_as_user
from nous_deploy.services import run_as_sudo
from fabric.utils import warn
from fabric.context_managers import prefix
from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.operations import put
from fabric.api import run


class VUtuti(Service):

    builds_dir = '/srv/ututi_builds'
    static_dir = '/srv/vututi/instance/static'

    @property
    def port(self):
        return self.settings['port']

    @property
    def host_name(self):
        return self.settings['host_name']

    @run_as_sudo
    def prepare(self):
        self.server.apt_get_install(' '.join([
                "build-essential",
                "enscript",
                "libfreetype6-dev",
                # "libjpeg62-dev",
                "liblcms1-dev",
                "libpq-dev",
                "libsane-dev",
                "libxml2-dev",
                "libxslt1-dev",
                "myspell-en-gb",
                "myspell-lt",
                "myspell-pl",
                "postgresql",
                "python-all",
                "python-all-dbg",
                "python-all-dev",
                "python-geoip",
                "python-pyrex",
                "python-setuptools",
                "uuid-dev",
                "zlib1g-dev",
                ]))
        package = "ututi-pg-dictionaries_1.0_all.deb"
        target_filename = os.path.join(self.server.getHomeDir(self.user), package)
        put(pkg_resources.resource_filename("nous_deploy.vututi", package),
            target_filename)
        run("dpkg -i %s" % target_filename)
        self.buildout_configure()
        # run("apt-get build-dep python-psycopg2 python-imaging")
        # apt-get remove python-egenix-mx-base-dev


    buildout_cache = '/srv/vututi/builds/cache'
    buildout_extends = '/srv/vututi/builds/extends'
    buildout_eggs = '/srv/vututi/builds/extends'
    @run_as_sudo
    def buildout_configure(self):
        dot_buildout = os.path.join(self.server.getHomeDir(self.user), ".buildout")
        for directory in [self.buildout_eggs,
                          self.buildout_extends,
                          self.buildout_cache,
                          dot_buildout]:
            run('mkdir -p %s' % directory)
            run('chown -R %s:%s %s' % (self.user, self.user, directory))

        buildout_config = os.path.join(dot_buildout, "default.cfg")
        self.upload_config_template("buildout_default.cfg",
                                    buildout_config, {'service': self})
        run('chown -R %s:%s %s' % (self.user, self.user, buildout_config))

    @run_as_sudo
    def configure(self):
        self.server.nginx_configure_site(self)
        # upload_config_template('%s.conf.py' % env.conf.PRODUCT_NAME,
        #                        os.path.join(instance_dir, '%s.conf.py' % env.conf.PRODUCT_NAME))
        # upload_config_template('supervisord.conf',
        #                        os.path.join(instance_dir, 'supervisord.conf'))
        # upload_config_template('elasticsearch.in.sh',
        #                        os.path.join(instance_dir, 'elasticsearch.in.sh'))
        # upload_config_template('elasticsearch.yml',
        #                        os.path.join(instance_dir, 'elasticsearch', 'config', 'elasticsearch.yml'))
        # upload_config_template('elasticsearch_logging.yml',
        #                        os.path.join(instance_dir, 'elasticsearch', 'config', 'logging.yml'))

    package_dir = '/mnt/vututi/packages'
    package_tmp_dir = '/mnt/vututi/packages/tmp'
    backups_dir = '/mnt/vututi/packages'

    build_dir = '/srv/vututi/builds' # a.k.a. code

    scripts_dir = '/srv/vututi/bin/'

    @run_as_sudo
    def create_site_dirs(self):
        for directory in [self.package_dir,
                          self.package_tmp_dir,
                          self.backups_dir,
                          self.build_dir,
                          self.scripts_dir]:
            run('mkdir -p %s' % directory)
            run('chown -R %s:%s %s' % (self.user, self.user, directory))

    @run_as_user
    def upload_release(self, release):
        put(release, self.package_dir)

    @run_as_sudo
    def setup(self, initial_release):
        self.server.ensure_user(self.user)
        self.create_site_dirs()

        self.upload_release(initial_release)
        self.build()

        create_instance_dirs()
        # instance_dir = os.path.join(env.conf.SITE_DIR, env.instance)
        # run("mkdir -p %s" % instance_dir)
        # with cd(instance_dir):
        #     run("mkdir -p bin" )
        #     run("mkdir -p elasticsearch/config")
        #     run("mkdir -p xapian")
        #     run("mkdir -p uploads/cms")
        #     run("mkdir -p var/run" )
        #     run("mkdir -p var/log/supervisord")
        upload_scripts()
        link_release()

        create_instance()
        # #!/bin/bash

        # . $PWD/bin/defaults.sh

        # mkdir -p $PWD/uploads
        # mkdir -p $PWD/cache
        # mkdir -p $PWD/db
        # $PG_PATH/bin/initdb -D $PWD/db -E UNICODE
        # mkdir -p $PWD/var/run
        # mkdir -p $PWD/var/log

        # $PG_PATH/bin/pg_ctl -D $PWD/db -o "-c unix_socket_directory=$PWD/var/run/ -c custom_variable_classes='ututi' -c ututi.active_user=0 -c default_text_search_config='public.lt'" start  -l $PWD/var/log/pg.log
        # sleep 5

        # $PG_PATH/bin/createuser --createdb --no-createrole --no-superuser --login admin -h $PWD/var/run
        # $PG_PATH/bin/createdb --owner admin -E UTF8 release -h $PWD/var/run
        # $PG_PATH/bin/createlang plpgsql release -h $PWD/var/run

        # $PG_PATH/bin/pg_ctl -D $PWD/db stop -o "-c unix_socket_directory=$PWD/var/run/"
        reset_database()
        # psql -h $PWD/var/run/ -d release -c "drop schema public cascade"
        # psql -h $PWD/var/run/ -d release -c "create schema public"
        # rm -rf $PWD/uploads
        # mkdir $PWD/uploads
        # code/bin/paster setup-app release.ini

        self.server.cron_setup(self)
        self.configure()

        # Cron
        # curl -s http://ututi.com/news/daily?date=`date -u +%Y-%m-%d` > /dev/null
        # curl -s http://ututi.com/news/hourly -F date=`date -u +%Y-%m-%d` -F hour=`date -u +%H` > /dev/null

        # import_db
        #!/bin/bash
        # . $PWD/bin/defaults.sh

        # psql -h $PWD/var/run/ -d release -c "drop schema public cascade"
        # psql -h $PWD/var/run/ -d release -c "create schema public"
        # $PG_PATH/bin/pg_restore -d release -h $PWD/var/run < $1/dbdump || true
        # rsync -rt $1/files_dump/uploads/ uploads/

        # ignas@avilys:/srv/ututi.com/instance$ cat bin/migrate.sh
        # #!/bin/bash
        # . $PWD/bin/defaults.sh
        # $PWD/code/bin/migrate release.ini


    @run_as_user
    def getLastPackagedRelease(self):
        return run("find %s | sort | tail -1" % self.package_dir).strip()

    build_db_port = 8862

    @run_as_user
    def build(self, rebuild=False):
        build_lock = os.path.join(self.build_dir, 'build.lock')
        if exists(build_lock) and not rebuild:
            warn("Package is being built aborting!")
            return

        run("touch %s" % build_lock)
        try:
            package_file = self.getLastPackagedRelease()
            release_name = os.path.basename(package_file).replace('.tar.gz', '')
            release_dir = os.path.join(self.build_dir, release_name)

            if exists(release_dir) and not rebuild:
                warn("Package has been built already run build:rebuild to rebuild it.")
                return

            if rebuild and exists(release_dir):
                run("rm -r %s" % release_dir)

            run("mkdir %s" % release_dir)
            run("tar -xvzf %s -C %s" % (package_file, self.build_dir))

            with cd(release_dir):
                with prefix("export PGPORT=%s" % self.build_db_port):
                    try:
                        run("make bin/paster compile-translations")
                        run("make start_database")
                        run("make test")
                    finally:
                        run("make stop_database")
                    run("rm -rf instance")
                    run("touch READY")
        finally:
            run("rm %s" % build_lock)

    @run_as_sudo
    def provision(self):
        pass
