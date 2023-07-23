## Topics

- [Install Prerequisites](#install-prerequisites)
- [Create K3s configuration](#create-k3s-configuration)
- [Setup K3s](#setup-k3s)
- [Setup Calico net](#setup-calico-net)

### Install Prerequisites

Update packages

```shell
apt-get update && apt-get dist-upgrade -y
```

Setup unattended upgrades

```shell
dpkg-reconfigure --priority=medium unattended-upgrades
```

Add swap for dev/CI setup

```shell
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo cp /etc/fstab /etc/fstab.bak
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Create K3s configuration

Create file `/etc/rancher/k3s/config.yaml` with following.

```yaml
write-kubeconfig-mode: "0644"
disable: traefik
cluster-init: true
flannel-backend: none
disable-network-policy: true
token: "changeit"
```

Place the file in all servers and agents.

### Setup K3s

Add odd number of server(s), start with 1.

```shell
curl -sfL https://get.k3s.io | sh -
```

Add agents (optional)

```shell
curl -sfL https://get.k3s.io | K3S_URL=https://${SERVER_IP}:6443 sh
```

Note: set `$SERVER_IP` to ip of the server / internal lb

### Setup Calico net

Source: https://projectcalico.docs.tigera.io/getting-started/kubernetes/k3s/quickstart

```shell
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.25.0/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.25.0/manifests/custom-resources.yaml
```
