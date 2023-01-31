## K3s + frappe framework with VS Code devcontainers

- [Provision K8s](#provision-k8s)
- [Provision Loadbalancer Service](#provision-loadbalancer-service)
- [Provision RWX StorageClass](#provision-rwx-storageclass)
- [Provision Database](#provision-database)
- [Setup ERPNext](#setup-erpnext)
- [Setup Bench Operator](#setup-bench-operator)
- [ReST API Call](#rest-api-call)
- [Teardown](#teardown)

### Provision K8s

For local development we'll use k3s in container. It can be used with VS Code devcontainer for ease of use.

Clone this repo and copy example directory to begin.

```shell
git clone https://github.com/castlecraft/custom_frappe_docker
cd custom_frappe_docker
cp -R kube-devcontainer .devcontainer
```

Reopen in VS Code devcontainer.
Or start `.devcontainer/compose.yml` and enter `frappe` container.

All the necessary cli tools and k3s based cluster will be available for development. `kubectl` and `git` plugin for zsh is also installed. Check or update the `.devcontainer/Dockerfile` for more.

### Provision Loadbalancer Service

Port 80 and 443 of k3s container is published but no service runs there. We'll add ingress controller which will simulate a LoadBalancer service and start serving port 80 and 443.

We're using ingress-nginx from https://kubernetes.github.io/ingress-nginx/deploy/#gce-gke. On installation it will add a LoadBalancer service to cluster and provision cloud load balancer from provider in production.

```shell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.5.1/deploy/static/provider/cloud/deploy.yaml
```

### Provision RWX StorageClass

In case of Production setup use HA file system like AWS EFS, Google Filestore, Managed NFS, Ceph, etc.
If you choose such service then backups, snapshots and restores are taken care of and no need for frappe/erpnext to manage it.

For local, evaluation, development or basic setup we will use in-cluster NFS server and provision Storage Class.

```shell
kubectl create namespace nfs
helm repo add nfs-ganesha-server-and-external-provisioner https://kubernetes-sigs.github.io/nfs-ganesha-server-and-external-provisioner
helm upgrade --install -n nfs in-cluster nfs-ganesha-server-and-external-provisioner/nfs-server-provisioner --set 'storageClass.mountOptions={vers=4.1}' --set persistence.enabled=true --set persistence.size=8Gi
```

Notes:

- Change the persistence.size from 8Gi to required specification.
- In case of in-cluster nfs server that runs in production make sure you setup a backup CronJob refer

<details>

<summary>cronjob.yaml</summary>

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ${CRONJOB_NAME}
  namespace: ${CRONJOB_NAMESPACE}
spec:
  schedule: "0 */12 * * *"
  jobTemplate:
    spec:
      backoffLimit: 0
      template:
        spec:
          securityContext:
            supplementalGroups: [1000]
          containers:
          - name: backup-and-push
            image: ${IMAGE}:${VERSION}
            command: ["bash", "-c"]
            args:
              - |
                bench --site all backup
                restic snapshots || restic init
                restic backup sites
                restic forget --group-by=paths --keep-last=30 --prune
            imagePullPolicy: IfNotPresent
            volumeMounts:
              - name: sites-dir
                mountPath: /home/frappe/frappe-bench/sites
            env:
              - name: RESTIC_REPOSITORY
                value: ${RESTIC_REPOSITORY}
              - name: "RESTIC_PASSWORD"
                valueFrom:
                  secretKeyRef:
                    key: resticPassword
                    name: ${CRONJOB_NAME}
              - name: "AWS_ACCESS_KEY_ID"
                valueFrom:
                  secretKeyRef:
                    key: accessKey
                    name: ${CRONJOB_NAME}
              - name: "AWS_SECRET_ACCESS_KEY"
                valueFrom:
                  secretKeyRef:
                    key: secretKey
                    name: ${CRONJOB_NAME}
          restartPolicy: OnFailure
          volumes:
            - name: sites-dir
              persistentVolumeClaim:
                claimName: erpnext-v14
                readOnly: false
---
apiVersion: v1
kind: Secret
metadata:
  name: ${CRONJOB_NAME}
  namespace: ${CRONJOB_NAMESPACE}
type: Opaque
stringData:
  resticPassword: ${RESTIC_PASSWORD}
  accessKey: ${AWS_ACCESS_KEY_ID}
  secretKey: ${AWS_SECRET_ACCESS_KEY}
```

Note: Change the number of restic snapshots to keep as per need.

Create `CronJob`

```shell
export CRONJOB_NAME=erpnext-backup
export CRONJOB_NAMESPACE=erpnext
export IMAGE=frappe/erpnext
export VERSION=v14
export RESTIC_REPOSITORY=s3:https://s3.endpoint.com/bucket-name/path-in-bucket
export RESTIC_PASSWORD=password
export AWS_ACCESS_KEY_ID=changeit
export AWS_SECRET_ACCESS_KEY=secret
cat cronjob.yaml | envsubst | kubectl apply -f -
```

</details>

### Provision Database

In case of production setup use AWS RDS, Google Sky SQL, or Managed MariaDB Service that is configurable for frappe specific param group properties. For simple or development setup we will install in-cluster MariaDB Helm chart with following command:

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

```shell
helm repo add frappe https://helm.erpnext.com
helm upgrade \
  --install frappe-bench \
  --namespace erpnext \
  frappe/erpnext \
  --set mariadb.enabled=false \
  --set dbHost=mariadb.mariadb.svc.cluster.local \
  --set dbPort=3306 \
  --set dbRootUser=root \
  --set dbRootPassword=admin \
  --set persistence.worker.enabled=true \
  --set persistence.worker.size=4Gi \
  --set persistence.worker.storageClass=nfs
```

### Setup Bench Operator

Install flux

```shell
flux install --components=source-controller,helm-controller
```

```shell
helm upgrade --install \
  --create-namespace \
  --namespace bench-system \
  --set api.enabled=true \
  --set api.apiKey=admin \
  --set api.apiSecret=changeit \
  --set api.createFluxRBAC=true \
  manage-sites k8s-bench/k8s-bench
```

Port forward kubernetes service locally on port 3000 for development setup. Store it in `site_config.json` and use to make python requests.

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
  "image": "frappe/erpnext:v14.13.0",
  "annotations": {
    "k8s-bench.castlecraft.in/job-type": "create-site",
    "k8s-bench.castlecraft.in/ingress-name": "frappe-localhost",
    "k8s-bench.castlecraft.in/ingress-namespace": "erpnext",
    "k8s-bench.castlecraft.in/ingress-host": "frappe.localhost",
    "k8s-bench.castlecraft.in/ingress-svc-name": "frappe-bench-erpnext",
    "k8s-bench.castlecraft.in/ingress-svc-port": "8080",
    "k8s-bench.castlecraft.in/ingress-annotations": "{\"kubernetes.io/ingress.class\":\"nginx\"}",
    "k8s-bench.castlecraft.in/ingress-cert-secret": "frappe-certificate-tls"
  }
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
  "image": "frappe/erpnext:v14.13.0",
  "annotations": {
    "k8s-bench.castlecraft.in/job-type": "delete-site",
    "k8s-bench.castlecraft.in/ingress-name": "frappe-localhost",
    "k8s-bench.castlecraft.in/ingress-namespace": "erpnext"
  }
}
'
```

Notes:

- Refer [K8s Bench docs](https://k8s-bench.castlecraft.in) for more.
- In case of frappe apps, add `k8s_bench_url`, `k8s_bench_key` and `k8s_bench_secret` in `site_config.json` and use it to make python `requests`. You can use the internal kubernetes service url e.g. `http://manage-sites-k8s-bench.bench-system.svc.cluster.local:8000` instead of exposing the api if your frappe app also resides on same cluster. In case of development setup, use the `http://0.0.0.0:3000` url after accessing it via `kubectl port-forward`

### Teardown

To teardown delete the helm releases one by one, wait for the pods to get deleted.

```shell
helm delete -n bench-system manage-sites
helm delete -n erpnext frappe-bench
helm delete -n mariadb mariadb
helm delete -n nfs in-cluster
kubectl delete pvc -n mariadb data-mariadb-0
kubectl delete pvc -n nfs data-in-cluster-nfs-server-provisioner-0
```
