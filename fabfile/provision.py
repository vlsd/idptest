"""
Functions for provisioning environments with fabtools (eat shit puppet!)
"""
# standard library
import sys
import copy
import os
from distutils.util import strtobool

# 3rd party
import fabric
from fabric.context_managers import quiet
from fabric.api import env, task, local, run, settings, cd, sudo, lcd
import fabtools
from fabtools.vagrant import vagrant_settings

# local
import decorators
import utils

@task
@decorators.needs_environment
def apt_get_update(max_age=86400*7):
    """refresh apt-get index if its more than max_age out of date
    """
    with vagrant_settings(env.host_string):
        try:
            fabtools.require.deb.uptodate_index(max_age=max_age)
        except AttributeError:
            msg = (
                "Looks like your fabtools is out of date. "
                "Try updating fabtools first:\n"
                "    sudo pip install fabtools==0.17.0"
            )
            raise Exception(msg)

@task
@decorators.needs_environment
def python_packages():
    """install python packages"""
    filename = os.path.join(utils.remote_project_root(), "REQUIREMENTS")
    with vagrant_settings(env.host_string):
        fabtools.require.python.requirements(filename, use_sudo=True)


@task
@decorators.needs_environment
def debian_packages():
    """install debian packages"""
    
    # get the list of packages
    filename = os.path.join(utils.project_root(), "REQUIREMENTS-DEB")
    with open(filename, 'r') as stream:
        packages = stream.read().strip().splitlines()

    # install them all with fabtools.
    with vagrant_settings(env.host_string):
        fabtools.require.deb.packages(packages)


@task
@decorators.needs_environment
def packages():
    """install all packages"""
    debian_packages()
    python_packages()


@task
@decorators.needs_environment
def setup_shell_environment():
    """setup the shell environment on the remote machine"""
    with vagrant_settings(env.host_string):

        # change into the /vagrant directory by default
        template = os.path.join(
            utils.fabfile_templates_root(),
            '.bash_profile',
        )
        fabtools.require.files.file(
            path="/home/vagrant/.bash_profile",
            contents="cd /vagrant",
        )


@task
@decorators.needs_environment
def setup_analysis():
    """prepare analysis environment"""
    with vagrant_settings(env.host_string):
        
        # write a analysis.ini file that has the provider so we can
        # easily distinguish between development and production
        # environments when we run our analysis
        template = os.path.join(
            utils.fabfile_templates_root(), 
            "server_config.ini",
        )
        fabtools.require.files.template_file(
            path="/vagrant/server_config.ini",
            template_source=template,
            context=env,
        )

        # create a data directory where all of the analysis and raw
        # data is stored. 
        data_dir = "/vagrant/data"
        fabtools.require.files.directory(data_dir)

@task
@decorators.needs_environment
def set_timezone(timezone):
    with vagrant_settings(env.host_string):
        sudo('echo "%s" > /etc/timezone' % timezone)
        sudo('dpkg-reconfigure --frontend noninteractive tzdata')
        fabtools.require.service.restarted('cron')


@task
@decorators.needs_environment
def require_timezone(timezone):
    with vagrant_settings(env.host_string):
        ret_code = 2
        with settings(warn_only=True):
            result = run('grep -q "^%s$" /etc/timezone' % timezone)
            ret_code = result.return_code
        if ret_code == 0:
            return
        elif ret_code == 1:
            set_timezone(timezone)
        else:
            raise SystemExit()


@task(default=True)
@decorators.needs_environment
def default(do_rsync=True):
    """run all provisioning tasks"""
    # http://stackoverflow.com/a/19536667/564709
    if isinstance(do_rsync, (str, unicode,)):
        do_rsync = bool(strtobool(do_rsync))

    # rsync files (Vagrant isn't doing any provisioning now)
    if do_rsync:
        local("vagrant provision %(host_string)s" % env)

    # run all of these provisioning tasks in the order specified here
    apt_get_update()

    # install debian packages first to make sure any compiling python
    # packages have necessary dependencies
    packages()

    # set time zone
    require_timezone('America/Chicago')

    # set up anything else that should be done on the virtual machine
    # to get it into the same state for everyone
    setup_shell_environment()
    setup_analysis()
