## Topics

- [Provision K8s](#provision-k8s)
- [Provision Loadbalancer Service](#provision-loadbalancer-service)
- [Provision RWX StorageClass](#provision-rwx-storageclass)
- [Provision Database](#provision-database)
- [Setup ERPNext](#setup-erpnext)
- [Setup Bench Operator](#setup-bench-operator)
- [ReST API Call](#rest-api-call)

### Provision K8s

For local testing we'll use k3d. For more information and installation guide refer https://k3d.io

```shell
k3d cluster create devcluster \
  --api-port 127.0.0.1:6443 \
  -p 80:80@loadbalancer \
  -p 443:443@loadbalancer \
  --k3s-arg "--disable=traefik@server:0" \
  --k3s-arg '--kubelet-arg=eviction-hard=imagefs.available<1%,nodefs.available<1%@agent:*' \
  --k3s-arg '--kubelet-arg=eviction-minimum-reclaim=imagefs.available=1%,nodefs.available=1%@agent:*' \
  --k3s-arg '--kubelet-arg=eviction-hard=imagefs.available<1%,nodefs.available<1%@server:0' \
  --k3s-arg '--kubelet-arg=eviction-minimum-reclaim=imagefs.available=1%,nodefs.available=1%@server:0'
```

### Provision Loadbalancer Service

We're using ingress-nginx from https://kubernetes.github.io/ingress-nginx/deploy/#gce-gke. On installation it will add a LoadBalancer service to cluster and provision cloud load balancer from provider.

```shell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.5.1/deploy/static/provider/cloud/deploy.yaml
```

### Provision RWX StorageClass

In case of Production setup use HA file system like AWS EFS, Google Filestore, Managed NFS, Ceph, etc.
If you choose such service then backups, snapshots and restores are taken care of and no need for frappe/erpnext to manage it.

For local, evaluation or basic setup we will use in-cluster NFS server and provision Storage Class.

```shell
kubectl create namespace nfs
helm repo add nfs-ganesha-server-and-external-provisioner https://kubernetes-sigs.github.io/nfs-ganesha-server-and-external-provisioner
helm upgrade --install -n nfs in-cluster nfs-ganesha-server-and-external-provisioner/nfs-server-provisioner --set 'storageClass.mountOptions={vers=4.1}' --set persistence.enabled=true --set persistence.size=8Gi
```

Notes:

- Change the persistence.size from 8Gi to required specification.
- In case of in-cluster nfs server make sure you setup a backup CronJob refer: https://gist.github.com/revant/2414cedce8e19d209d5d337ea19efabc


### Provision Database

In case of production setup use AWS RDS, Google Sky SQL, or Managed MariaDB Service that is configurable for frappe specific param group properties.

```shell
export FRAPPE_MARIADB_CNF=$(cat <<EOF
[mysqld]
character-set-client-handshake=FALSE
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
skip-name-resolve
explicit_defaults_for_timestamp
basedir=/opt/bitnami/mariadb
plugin_dir=/opt/bitnami/mariadb/plugin
port=3306
socket=/opt/bitnami/mariadb/tmp/mysql.sock
tmpdir=/opt/bitnami/mariadb/tmp
max_allowed_packet=16M
bind-address=*
pid-file=/opt/bitnami/mariadb/tmp/mysqld.pid
log-error=/opt/bitnami/mariadb/logs/mysqld.log
collation-server=utf8mb4_unicode_ci
slow_query_log=0
slow_query_log_file=/opt/bitnami/mariadb/logs/mysqld.log
long_query_time=10.0
[client]
port=3306
socket=/opt/bitnami/mariadb/tmp/mysql.sock
default-character-set=utf8mb4
plugin_dir=/opt/bitnami/mariadb/plugin
[manager]
port=3306
socket=/opt/bitnami/mariadb/tmp/mysql.sock
pid-file=/opt/bitnami/mariadb/tmp/mysqld.pid
EOF
)

kubectl create namespace mariadb
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install mariadb -n mariadb bitnami/mariadb \
  --set architecture=standalone \
  --set auth.rootPassword=admin \
  --set auth.database=my_database \
  --set auth.username=my_database \
  --set auth.password=admin \
  --set auth.replicationUser=replicator \
  --set auth.replicationPassword=admin \
  --set primary.configuration=$FRAPPE_MARIADB_CNF
```

### Setup ERPNext

Create image registry secret in erpnext namespace

```shell
kubectl create namespace erpnext

kubectl -n erpnext create secret docker-registry ghcr-cred \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USER \
  --docker-password=$GITHUB_PAT
```

Note: Replace `ghcr.io`, `$GITHUB_USER` and `$GITHUB_PAT` with your credentials.

```shell
helm repo add frappe https://helm.erpnext.com
helm upgrade \
  --install frappe-bench \
  --namespace erpnext \
  frappe/erpnext \
  --set imagePullSecrets\[0\].name=ghcr-cred \
  --set mariadb.enabled=false \
  --set dbHost=mariadb.mariadb.svc.cluster.local \
  --set dbPort=3306 \
  --set dbRootUser=root \
  --set dbRootPassword=admin \
  --set nginx.image.repository=ghcr.io/castlecraft/custom_frappe_docker/nginx \
  --set nginx.image.tag=1.0.0 \
  --set worker.image.repository=ghcr.io/castlecraft/custom_frappe_docker/worker \
  --set worker.image.tag=1.0.0 \
  --set persistence.worker.enabled=true \
  --set persistence.worker.size=4Gi \
  --set persistence.worker.storageClass=nfs
```

Note: Use `imagePullSecrets` only if image registry is private and needs auth with credentials.

### Setup Bench Operator

```shell
helm upgrade --install \
  --create-namespace \
  --namespace bench-system \
  --set api.enabled=true \
  --set api.apiKey=admin \
  --set api.apiSecret=changeit \
  manage-sites k8s-bench/k8s-bench
```

Port forward kubernetes service locally on port 3000.

```shell
kubectl port-forward -n bench-system svc/manage-sites-k8s-bench 3000:8000
```

### ReST API Call

Create Site:

```shell
curl -X POST -u admin:changeit http://0.0.0.0:3000/bench-command \
    -H 'Content-Type: application/json' \
    -d '{
  "job_name": "create-frappe-local",
  "sites_pvc": "frappe-bench-erpnext",
  "args": [
    "bench",
    "new-site",
    "--admin-password=admin",
    "--db-root-password=admin",
    "--force",
    "frappe.localhost"
  ],
  "command": null,
  "logs_pvc": null,
  "namespace": "erpnext",
  "worker_image": "frappe/erpnext-worker:v14.2.3",
  "nginx_image": "frappe/erpnext-nginx:v14.2.3",
  "annotations": {
    "k8s-bench.castlecraft.in/job-type": "create-site",
    "k8s-bench.castlecraft.in/ingress-name": "frappe-localhost",
    "k8s-bench.castlecraft.in/ingress-namespace": "erpnext",
    "k8s-bench.castlecraft.in/ingress-host": "frappe.localhost",
    "k8s-bench.castlecraft.in/ingress-svc-name": "frappe-bench-erpnext",
    "k8s-bench.castlecraft.in/ingress-svc-port": "8080",
    "k8s-bench.castlecraft.in/ingress-annotations": "{\"kubernetes.io/ingress.class\":\"nginx\"}",
    "k8s-bench.castlecraft.in/ingress-cert-secret": "frappe-certificate-tls"
  },
  "populate_assets": true
}
'
```

Delete Site:

```shell
curl -X POST -u admin:changeit http://0.0.0.0:3000/bench-command \
    -H 'Content-Type: application/json' \
    -d '{
  "job_name": "delete-frappe-local",
  "sites_pvc": "frappe-bench-erpnext",
  "args": [
    "bench",
    "drop-site",
    "--db-root-password=admin",
    "--archived-sites-path=deleted-sites",
    "--no-backup",
    "--force",
    "frappe.localhost"
  ],
  "command": null,
  "logs_pvc": null,
  "namespace": "erpnext",
  "worker_image": "frappe/erpnext-worker:v14.2.3",
  "nginx_image": "frappe/erpnext-nginx:v14.2.3",
  "annotations": {
    "k8s-bench.castlecraft.in/job-type": "delete-site",
    "k8s-bench.castlecraft.in/ingress-name": "frappe-localhost",
    "k8s-bench.castlecraft.in/ingress-namespace": "erpnext"
  },
  "populate_assets": true
}
'
```

Notes:

- Refer [K8s Bench docs](https://k8s-bench.castlecraft.in) for more.
- In case of frappe apps, add `k8s_bench_url`, `k8s_bench_key` and `k8s_bench_secret` in `site_config.json` and use it to make python `requests`. You can use the internal kubernetes service url e.g. `http://manage-sites-k8s-bench.bench-system.svc.cluster.local:8000` instead of exposing the api if your frappe app also resides on same cluster.

## Teardown

To teardown delete the helm releases one by one, wait for the pods to get deleted.

```shell
helm delete -n bench-system manage-sites
helm delete -n erpnext frappe-bench
helm delete -n mariadb mariadb
helm delete -n nfs in-cluster
kubectl delete pvc -n mariadb data-mariadb-0
kubectl delete pvc -n nfs data-in-cluster-nfs-server-provisioner-0
k3d cluster delete devcluster
```
