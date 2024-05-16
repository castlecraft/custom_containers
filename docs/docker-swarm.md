## Topics

- [Install Prerequisites](#install-prerequisites)
- [Setup Docker Swarm](#setup-docker-swarm)
- [Setup Traefik](#setup-traefik)
- [Setup Portainer](#setup-portainer)
- [Setup MariaDB](#setup-mariadb)
- [Setup Swarm CRON](#setup-swarm-cron)
- [Setup ERPNext](#setup-erpnext)

### Install Prerequisites

These steps are required for production server. For dind/local setup copy `dind-devcontainer` to `.devcontainer` and reopen in devcontainer.

Use files from `compose` directory.

Setup assumes you are using Debian based Linux distribution.

Update packages

```shell
apt-get update && apt-get dist-upgrade -y
```

Setup unattended upgrades

```shell
dpkg-reconfigure --priority=medium unattended-upgrades
```

Add non-root sudo user

```shell
adduser -D ubuntu
usermod -aG sudo ubuntu
curl -fsSL https://get.docker.com | bash
usermod -aG docker ubuntu
su - ubuntu
```

Clone this repo

```shell
git clone https://github.com/castlecraft/custom_containers
cd custom_containers
```

Note: traefik and portainer yamls specified in the further commands are in `compose` directory.

### Setup Docker Swarm

Initialize swarm

```shell
docker swarm init --advertise-addr=X.X.X.X
```

Note: Make sure the advertise-address does not change if you wish to add multiple nodes to this manager.

Comprehensive guide available at [dockerswarm.rocks](https://dockerswarm.rocks)

### Setup Traefik

Label the master node to install Traefik

```shell
docker node update --label-add traefik-public.traefik-public-certificates=true $(docker info -f '{{.Swarm.NodeID}}')
```

Set email and traefik domain

```shell
export EMAIL=admin@example.com
export TRAEFIK_DOMAIN=traefik.example.com
# or for dind
export TRAEFIK_DOMAIN=traefik.localhost
```

Set `HASHED_PASSWORD`

```shell
export HASHED_PASSWORD=$(openssl passwd -apr1)
Password: $ enter your password here
Verifying - Password: $ re enter your password here
```

Note:

Install Traefik in production

```shell
docker stack deploy -c compose/traefik-host.yml traefik
```

Install Traefik in dind

```shell
source /workspace/dind-devcontainer/setup-docker-env.sh
docker stack deploy -c /workspace/compose/traefik-dind.yml traefik
```

More on [Traefik](https://dockerswarm.rocks/traefik/)

### Setup Portainer

Label the master node to install portainer

```shell
docker node update --label-add portainer.portainer-data=true $(docker info -f '{{.Swarm.NodeID}}')
```

Set portainer domain

```shell
export PORTAINER_DOMAIN=portainer.example.com
# or
export PORTAINER_DOMAIN=portainer.localhost
```

Install Portainer in production

```shell
docker stack deploy -c compose/portainer.yml portainer
```

Install Portainer in dind

```shell
docker stack deploy -c /workspace/compose/portainer-dind.yml portainer
```

<details>

<summary>Additional commands for dind only</summary>

Initialize portainer

```shell
export PORTAINER_PASSWORD=supersecretpassword
http POST https://docker/api/users/admin/init "Host: portainer.localhost" Username="admin" Password="${PORTAINER_PASSWORD}" --follow --verify=no
```

Get bearer token

```shell
export TOKEN=$(http POST https://docker/api/auth "Host: portainer.localhost" Username=admin Password=${PORTAINER_PASSWORD} --follow --verify=no | jq -r .jwt)
```

Add endpoint

```shell
source /workspace/dind-devcontainer/setup-docker-env.sh
http POST \
  https://docker/api/endpoints \
  "Authorization:Bearer $TOKEN" \
  "Host:portainer.localhost" \
  Name=dind EndpointCreationType=1 URL=tcp://$DOCKER_API \
  --follow \
  --form \
  --verify=no
```

</details>

More on [portainer](https://dockerswarm.rocks/portainer)

### Setup MariaDB

- Go to Stacks > Add and create stack called `mariadb`.
- Set `DB_PASSWORD` environment variable to set mariadb root password. Defaults to `admin`.
- Use `compose/mariadb.yml` to create the stack.

### Setup Swarm CRON

In case of docker setup there is not CRON scheduler running. It is needed to take periodic backups.

- Go to Stacks > Add and create stack called `swarm-cron`.
- Use `compose/swarm-cron.yml` to create the stack.
- Change the `TZ` environment variable as per your timezone.

### Setup ERPNext

- `compose/erpnext.yml`: Use to create the `erpnext` stack. Set `VERSION` to version of choice. e.g. `v14.13.0`. Set `SITES` variable as list of sites quoted in back tick  (`` ` ``) and separated by comma (`,`). Example ``SITES=`one.example.com`,`two.example.com` ``. Set `BENCH_NAME` optionally in case of multiple benches, defaults to `erpnext`.
- `compose/configure-erpnext.yml`: Use to setup `sites/common_site_config.json`. Set `VERSION` and optionally `BENCH_NAME` environment variables.
- `compose/create-site.yml`: Use to create a site. Set `VERSION` and optionally `BENCH_NAME` environment variables. Change the command for site name, apps to be installed, admin password and db root password.
- `compose/erpnext-backup.yml`: Use to backup and push snapshots. Set environment variables mentioned in comments in the file.
