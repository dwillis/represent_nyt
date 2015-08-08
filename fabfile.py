"""
Fabric deployment utility

Default settings are to deploy on jeffvader to /home/dwillis/projects, but these can be altered as needed.

Usage:

fab deploy_stage # for jeffvader
fab deploy_prod  # for ec2

"""

set(
    fab_hosts = ['##########'],
    repo = '/svn/django/trunk',
    path = '/home/dwillis/projects', # change this if deploying to another location
    fab_user = 'dwillis', # change this if deploying to another user's directory
    tmp_path = '/tmp/represent/',
)

# deploy to EC2 instance
# will need to change
def deploy_prod():
    local("svn export -q $(repo) $(tmp_path) --force")
    local("tar -C $(tmp_path) -c -z -f represent.tar.gz .")
    set(env='production')
    set(fab_hosts = ['#######'])
    set(fab_user = 'root')
    set(fab_key_filename='########') # need full path here; change as needed
    put("represent.tar.gz", '/home/dwillis/represent.tar.gz')
    run("cd /home/dwillis; cp -r projects/ releases/; rm -rf projects; mkdir projects; tar -C $(path) -x -z -f represent.tar.gz; rm represent.tar.gz")
    run("cd /var/tmp/django_cache; sudo rm -rf *")
    reboot()

# remove latest version and replace with previous version
def rollback_prod():
    set(env='production')
    set(fab_hosts = ['########'])
    set(fab_user = 'root')
    set(fab_key_filename='##########') # need full path here; change as needed
    run("cd /home/dwillis; rm -rf projects; cp -r releases/projects .")
    run("cd /var/tmp/django_cache; sudo rm -rf *")
    reboot()

# deploy to jeffvader defaults - change global settings above if another location
def deploy_stage():
    run("cd $(path); svn up")
    reboot()

def reboot():
    sudo("apache2ctl graceful")
