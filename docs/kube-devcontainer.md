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
git clone https://github.com/castlecraft/custom_containers
cd custom_containers
cp -R kube-devcontainer .devcontainer
```

Reopen in VS Code devcontainer.
Or start `.devcontainer/compose.yml` and enter `frappe` container.

All the necessary cli tools and k3s based cluster will be available for development. `kubectl` and `git` plugin for zsh is also installed. Check or update the `.devcontainer/Dockerfile` for more.

### Provision Loadbalancer Service

Port 80 and 443 of k3s container is published but no service runs there. We'll add ingress controller which will simulate a LoadBalancer service and start serving port 80 and 443.

We're using ingress-nginx from https://kubernetes.github.io/ingress-nginx/deploy/#gce-gke. On installation it will add a LoadBalancer service to cluster and provision cloud load balancer from provider in production.

```shell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
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
  --set primary.extraFlags="--skip-character-set-client-handshake --skip-innodb-read-only-compressed --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci" \
  --wait
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
  --set persistence.worker.storageClass=nfs \
  --set jobs.configure.fixVolume=false \
  --set jobs.createSite.enabled=true \
  --set jobs.createSite.siteName=erpnext.localhost \
  --set ingress.enabled=true \
  --set ingress.className=nginx \
  --set "ingress.hosts[0].host=erpnext.localhost" \
  --set "ingress.hosts[0].paths[0].pathType=ImplementationSpecific" \
  --set "ingress.hosts[0].paths[0].path=/"
```

### Teardown

To teardown delete the helm releases one by one, wait for the pods to get deleted.

```shell
helm delete -n erpnext frappe-bench
helm delete -n mariadb mariadb
helm delete -n nfs in-cluster
kubectl delete pvc -n mariadb data-mariadb-0
kubectl delete pvc -n nfs data-in-cluster-nfs-server-provisioner-0
```
