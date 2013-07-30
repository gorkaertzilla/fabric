"""
Egilea:         gorka ercilla, ercillagorka@gmail.com
server:         Ubuntu 12.04
Zer egiten du:
             1) Linux eta python pakete guztiak instalatzen ditu django projectua martzan jartzeko ubuntu serbidore batetan.
             2) Edo zure ordenagailu lokalean dituzun aldaketak edo githubean dituzun aldaketak serbidorean eguneratzen ditu.

Zer egiten du: Script honek fabric instalatuta eukitzea eskatzen dotzu. => (http://docs.fabfile.org/en/1.7/)
              fabric tresna aukera ematen deu script berean, tokiko eta urruneko komandoak ejekutatzeko eta hedapena gidoiak sortzeko
              Script honek (fabfile.py) projektuaren karpetan egon behar da:
              1) Urruneko zerbitzari batera konektatuko da eta zure Django proiektua hedatzeko behar diren paketeak instalatuko ditu Ubuntu sistema batetan.
                 ==> Python paketeak PIP bidez instalatuko dira (http://www.pip-installer.org/) virtualenv ingurunean eta virtualenvwrapper erabiliz (tualenvwrapper.readthedocs.org).
                        PIP badaki zer instalatu behar duen proiektuaren karpetan requirements.txt fitxeroan jarrita dagoelako. (fabfile.py dagoen karpetan)
                 ==> Python paketeak ez dira, ohi bezala instalatutako Ubuntu zerbitzarian.
              2) Zip zure git proiektua eta kopiatu urruneko zerbitzaria, sortu "bertsioa" karpeta eta deskonprimitu kodea han.
                  Urruneko karpeta jada existitzen bada huts egingo du.
              3) Instalatu zure aplikazioa nginx eta gunicorn zerbitzarian
"""

from fabric.api import *
import os

# globals
env.project_name = 'webme'
env.fabfile_path = os.path.dirname(os.path.realpath(__file__))


def environment():
    #     Erabiltzaile lokala, ta bardine serbidorean errazago izateko.
    env.user = 'gorka'
    env.email = 'ercillagorka@gmail.com'
    env.repository = 'git@github.com:ercillagorka/syte.git'
    #     Serbitzariaren ip-a, bat baino gehiago izen al da [192.168.14.1 , 192.168.14.2 , 192.168.14.3]
    env.hosts = ['184.106.152.183']
    env.deploy_user = 'gorka'
    #     virtualenv egongo dan lekua
    env.virtualenv = '$HOME/.virtualenvs'
    #     virtualenv proiektuaren izena
    env.virtualenvwrapper = env.project_name
    #     virtuallenvwrapper aktibetako
    env.activate = 'workon %(virtualenvwrapper)s' % env
    #     permisoak aldatuteko
    env.code_root_parent = "/var/www"
    env.code_root = '/var/www/'
    #     whole_path /var/www/webme/
    #     proiektuaren lekua
    env.whole_path = "%(code_root_parent)s/%(project_name)s/" % (env)


def reset_permissions():
    sudo('chown %(user)s -R %(code_root_parent)s' % env)
    sudo('chgrp %(user)s -R %(code_root_parent)s' % env)


def reset_permissions_path():
    sudo('chown %(user)s -R %(whole_path)s' % env)
    sudo('chgrp %(user)s -R %(whole_path)s' % env)


def configure_git():
    sudo('git config --global user.name "%(user)s"' % env)
    sudo('git config --global use.email "%(email)s"' % env)
    sudo('ssh-keygen -t rsa -C "%(email)s"' % env)


def setup():
    require('hosts', provided_by=[environment])
    print("Executing on %(hosts)s as %(user)s" % env)
    sudo('apt-get install -y git python python-dev python-pip python-setuptools nginx-full postgresql libpq-dev')
    sudo('mkdir -p %(code_root)s' % env)
    configure_git
    virtualenvwrapper_config()
    reset_permissions()
    deploy()


def virtualenvwrapper_config():
    sudo('pip install virtualenv')
    sudo('pip install virtualenvwrapper')
    sudo('export WORKON_HOME=$HOME/.virtualenvs')
    sudo('mkdir -p $WORKON_HOME')
    sudo('source /usr/local/bin/virtualenvwrapper.sh')
    sudo("export VIRTUALENVWRAPPER_VIRTUALENV_ARGS='--no-site-packages'")


def deploy():
    require('hosts', provided_by=[environment])
    require('whole_path', provided_by=[environment])
    require('code_root')
    # whole_path /var/www/webme/
    sudo('mkdir -p %(whole_path)s ; cd %(whole_path)s' % env)
    download_git_repository()
    install_requirements()
    Configure_Nginx
    sudo('python manage.py syncdb')
    live_gunicorn_Supervisor()
    restart_webserver()


def download_git_repository():
    require('whole_path', provided_by=[environment])
    sudo('cd %(whole_path)s' % env)
    sudo('git clone %(repository)s' % env)


def install_requirements():
    require('whole_path', provided_by=[deploy, setup])
    sudo('cd %(whole_path)s; pip install -E . -r /requirements.txt' % env)
    reset_permissions()


def Configure_Nginx():
    require('whole_path', provided_by=[deploy, setup])
    sudo('rm -f /etc/nginx/sites-enabled/default')
    put('%(fabfile_path)s/neat', '/etc/nginx/sites-available/' % env)
    sudo('ln -s /etc/nginx/sites-available/neat /etc/nginx/sites-enabled/neat')
    reset_permissions_path


def live_gunicorn_Supervisor():
    require('whole_path', provided_by=[deploy, setup])
    put('%(fabfile_path)s/%(project_name)s.conf', '/etc/supervisor/conf.d/' % env)


def restart_webserver():
    sudo('sudo supervisorctl reread; sudo supervisorctl update')
    sudo('sudo supervisorctl status')
    sudo('sudo service nginx restart')
