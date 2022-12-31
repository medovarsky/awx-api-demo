# AWX API demo

## Purpose

This demo contains complete Infrastructure as a Code (IaaC) software repository which brings Kubernetes (K8s) environment to bare Ubuntu 22.04 Server, and up to a running AWX instance.

The goal of this demo is to build Ansible AWX platform by running Ansible playbook contained in this Git repository, as well as demonstrate running Ansible playbook through AWX API.

AWX playbook itself is idempotent, and running it multiple times has no unintended behavior on an AWX instance nor its data.

The demo consists of the following logical parts:
1. Ansible playbook which installs Kubernetes and AWX,
2. Configuring AWX in UI for parts which have not been automated for purposes of this demo. The configuration could be automated using AWX API calls.
3. Running API calls through included Python demo application.


# IaaC demo code

Prerequisites:

1. Instance of Ubuntu 22.04 server with SSH daemon running and root access,
2. Working internet connection or correctly propagated proxy and CA certificate import, as needed.

## Preparing for demo

AWX playbook is conveniently stored in this Git repository. It is advised to clone the repository to Ansible server in destination environment:

    git clone https://github.com/medovarsky/awx-api-demo.git
    cd  awx-api-demo

While IaaS has all the code needed for AWX to be built, it needs configuration defaults to be altered to suit our needs. The following files need to be revised:
* `hosts/minikube.yml` – contains connection to host to become Kubernetes platform for AWX instance. You can also predefine host name and connection details in your ~/.ssh/config.
* `group_vars/minikube.yml` – contains non-privileged user and group (defaults to kubes:kubes), as well as Kubernetes CPU (3) and RAM (2200m) settings. You can also define your public key for non-privileged user at destination host. For this demo, the public key will be defined at command line.
* `ansible.cfg`, in case any special configuration is needed for whole Demo project, like turning cowsay on.

From now on, a working network connectivity is required. Ansible should be installed in Python 3 virtual environment, in CLI, inside awx-api-demo directory:

    python3 -m venv . # if this fails, install python3 venv package and retry
    source bin/activate # enter virtual environment
    pip install -U pip # update package installer
    pip install wheel # package installer helper
    pip install ansible # also installs dependencies

At this point, we are ready to run awx.yml playbook.

    ansible-playbook -i hosts/minikube.yml awx.yml -e "minikube_ssh_public_key='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILnjMCnh6jl2SWenu5XiWwXf7cP3U4Jl7dQXpP2RCwXq kubes@pc'"

Where `minikube_ssh_public_key` contains public key one-liner to be added to user‘s `~/.ssh/authorized_keys` file.

The playbook makes the following changes to destination host(s):

1. installs mail utilities and Docker as Kubernetes back-end (as root),
2. configures non-privileged user and group, adds passwordless sudo privilege as well as docker secondary group membership (as root),
3. installs minikube Kubernetes runtime and kustomize tool for easier K8s resource definition,
4. Creates an instance of AWX Operator Controller Manager (as in https://github.com/ansible/awx-operator) and waits for its readiness,
5. Adds AWX instance and waits for its readiness,
6. Retrieves AWX URL and waits for it to become available.
7. Retrieves admin password and writes it to the console.

If admin password is needed afterwards, the following command will retrieve it:

    kubectl get secret awx-demo-admin-password -o jsonpath="{.data.password}" | base64 --decode ; echo

Connection URL is always retrievable using:

    minikube service -n awx awx-demo-service --url

For demonstration purposes, Minikube system service is not started at boot time. It can be started using the following command:

    minikube start

and stopped manually using:

    minikube stop

The configuration data is persistent through subsequent minikube restarts.

At this point, AWX is ready for manual configuration part.


# Manual configuration

For external users to be able to execute playbooks, the following resources within AWX need to be defined:

1. Organization where the resources will be locked into.
2. Credential for Git repository,
3. Credential for host from where Ansible playbook will get demo information or make changes to it through AWX API,
4. API Team for Execute Access,
5. Non-privileged API user,
6. Host inventory,
7. Demo Project,
8. Demo Template.

### The following changes are needed in UI:

    Access/Organization, Add:
    Name: ExampleCompany
    Execution Environment: AWX EE (latest)
    Save

    Access/Teams, Add:
    Name: DemoTeam
    Organization: DemoCompany
    Save

    Access/Users, Add:
    Username: DemoUser
    Password: <>
    Confirm Password: <>
    User Type: Normal User
    Organization: DemoCompany
    Save
    tab: Teams
    Select DemoTeam
    Associate

    Resources/Credentials, Add
    Name: Demo repository
    Description: „only private key auth is usable!“
    Organization: DemoCompany
    Credential type: Source Control
    SCM Private Key: create and paste private key for AWX user to access Git repository
    Private Key Passphrase: enter if needed
    Save

    Resources/Credentials, Add
    Name: Demo machine credentials
    Organization: DemoCompany
    Username: <ansible service user name>
    Credential Type: Machine
    Private Key Passphrase: enter if needed
    Privilege Escalation Password: enter if needed
    Save

    Resources/Projects, Add
    Name: Demo project
    Organization: DemoCompany
    Source control type: Git
    Source Control URL: https://github.com/medovarsky/awx-smax-demo.git
    Source Control Branch/Tag/Commit: master
    Source Control Credential: Demo repository (not needed for public r/o access)
    Options: Delete
    Save
    tab: Access – verify that API user has „Use“ access

    Resources/Templates, Add/Add job template
    Name: Demo Templates
    Job Type: Run
    Inventory: Demo
    Project: Demo Projects
    Credentials: „SSH:Demo Machine Credentials“
    tab: Access
    DemoUser = Execute
    Save

# API Demo

To make the demo user friendly, a demo application run_job.py was written in Python. It is up to the user to choose where to run it from – whether from Kubernetes host where AWX is running, or by opening a forwarding connection from demo host‘s public-facing IP address.
For cloning demo repository, please refer to Chapter 1.

Before running API demo, server URL and user credentials should be checked:

    vi run_job.py

Items of interest:

    template_id = 10 # from URL of Resources/Templates/Demo Template in UI
    tls_verify = False # for HTTPS connections
    host_url = 'http://192.168.49.2:30080/api/v2' # must include /api/v2 path
    awx_user = 'apidemo'
    awx_password = 'apidemo'

After the settings are checked and correct, the demo can be executed with optional template id:

    python3 run_job.py [template_id]

At the end of a CLI session within virtual environment, enter:

    deactivate


# Final remarks

If you have no kc alias, you can execute:

    alias kc=‘minikube kubectl --‘

or add it to your `~/.bash_aliases` to load at your next login. The playbook does this for its kubes user.

Useful commands for Kubernetes environment:

    kc logs -f deployments/awx-operator-controller-manager -c awx-manager

    kc get pods -o json |grep name |grep task

    kc get pods -n awx #list pods in awx namespace

    kc exec -i -t pod/awx-demo-${container_id} --container awx-demo-task – bash
