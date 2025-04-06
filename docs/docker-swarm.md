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

More on [Traefik](https://dockerswarm.rocks/traefik/)

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

Install Traefik in production

```shell
docker stack deploy -c compose/traefik-host.yml traefik
```

<details>

<summary>Install Traefik in dind</summary>

```shell
source /workspace/dind-devcontainer/setup-docker-env.sh
docker stack deploy -c /workspace/compose/traefik-dind.yml traefik
```

</details>

### Setup Portainer

More on [portainer](https://dockerswarm.rocks/portainer)

Label the master node to install portainer

```shell
docker node update --label-add portainer.portainer-data=true $(docker info -f '{{.Swarm.NodeID}}')
```

Install Portainer in production

```shell
# Set domain
export PORTAINER_DOMAIN=portainer.example.com
# Install
docker stack deploy -c compose/portainer.yml portainer
```

<details>

<summary>Install Portainer in dind</summary>

```shell
# Set domain
export PORTAINER_DOMAIN=portainer.localhost
# Install
docker stack deploy -c /workspace/compose/portainer-dind.yml portainer
```

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

- `compose/erpnext.yml`: Use to create the `erpnext` stack. Set variable names mentioned in the YAML comments.
- `compose/configure-erpnext.yml`: Use to setup `sites/common_site_config.json`. Set `VERSION` and optionally `BENCH_NAME` environment variables.
- `compose/create-site.yml`: Use to create a site. Set `VERSION` and optionally `BENCH_NAME` environment variables. Change the command for site name, apps to be installed, admin password and db root password.


### Advance Configuration

#### Nginx max body size:

refer: https://github.com/nginx-proxy/nginx-proxy/issues/690#issuecomment-275560780

Add `config`:

```
client_max_body_size 0;
```

Attach config in `erpnext.yml` on `frontend` service:

```yaml
services:
  # ...
  frontend:
    # ...
    configs:
      - source: nginx-body-size-disable
        target: /etc/nginx/conf.d/disable_mbs.conf
        uid: "1000"
        gid: "1000"
        mode: 0440
  # ...

configs:
  nginx-body-size-disable:
    external: true
```

#### Set limits and reservation / requests

```yaml
services:
  backend:
    <<: *custom_image
    deploy:
      # ...
      resources:
        limits:
          cpus: '0.5'
          memory: 650M
```
