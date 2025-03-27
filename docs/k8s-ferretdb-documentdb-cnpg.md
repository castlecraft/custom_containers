### Install CloudNativePG Operator.

Refer official [README](https://cloudnative-pg.io/charts).

```shell
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm upgrade --install cnpg \
  --namespace cnpg-system \
  --create-namespace \
  cnpg/cloudnative-pg
```

### Create PostgreSQL Cluster using ghcr.io/ferretdb/postgres-documentdb image

postgres-documentdb is required for FerretDB v2.

```shell
kubectl create ns ferretdb
kubectl apply -f postgres-cluster.yaml -n ferretdb
```

<details>

<summary>postgres-cluster.yaml</summary>

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: ferretdb-cnpg
  labels:
    app.kubernetes.io/component: database
    app.kubernetes.io/version: 17.0-bookworm
spec:
  instances: 3
  description: "ferretdb DB"
  imageName: "ghcr.io/ferretdb/postgres-documentdb:17-0.102.0-ferretdb-2.0.0"

  primaryUpdateStrategy: unsupervised
  postgresGID: 999
  postgresUID: 999
  enableSuperuserAccess: true
  postgresql:
    shared_preload_libraries:
      - pg_cron
      - pg_documentdb_core
      - pg_documentdb
      - pg_stat_statements

    parameters:
      cron.database_name: "postgres"

  bootstrap:
    initdb:
      postInitSQL:
        - "CREATE EXTENSION IF NOT EXISTS documentdb CASCADE;"

  storage:
    storageClass: local-path
    size: 20Gi

  walStorage:
    storageClass: local-path
    size: 20Gi

  monitoring:
    enablePodMonitor: false

  # see https://cloudnative-pg.io/documentation/1.22/kubernetes_upgrade/
  nodeMaintenanceWindow:
    reusePVC: false # rebuild from other replica instead
```

</details>

### Get postgres password to set in FERRETDB_POSTGRESQL_URL

```shell
export FERRETDB_POSTGRESQL_URL=postgres://postgres:$(kubectl get secret -n ferretdb ferretdb-cnpg-superuser -o jsonpath='{.data.password}' | base64 -d)@ferretdb-cnpg-rw:5432/postgres
```

### Create FerretDB deployment and service

```shell
envsubst < ferretdb.yaml | kubectl -n ferretdb apply -f -
```

<details>

<summary>ferretdb.yaml</summary>

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ferretdb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ferretdb
  template:
    metadata:
      labels:
        app: ferretdb
    spec:
      containers:
        - name: ferretdb
          image: ghcr.io/ferretdb/ferretdb:latest
          ports:
            - containerPort: 27017
          env:
            - name: FERRETDB_POSTGRESQL_URL
              value: ${FERRETDB_POSTGRESQL_URL}
---
apiVersion: v1
kind: Service
metadata:
  name: ferretdb-service
spec:
  selector:
    app: ferretdb
  ports:
    - name: mongo
      protocol: TCP
      port: 27017
      targetPort: 27017
```

</details>

### Port forward FerretDB service

```shell
kubectl port-forward -n ferretdb svc/ferretdb-service 27017:27017
```

### Access FerretDB service using mongosh

```shell
mongosh "mongodb://postgres:$(kubectl get secret -n ferretdb ferretdb-cnpg-superuser -o jsonpath='{.data.password}' | base64 -d)@localhost/postgres"

Current Mongosh Log ID: 67e37ad08c20d3ff5b6b140a
Connecting to:          mongodb://<credentials>@localhost/postgres?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2
Using MongoDB:          7.0.77
Using Mongosh:          2.4.2

For mongosh info see: https://www.mongodb.com/docs/mongodb-shell/

------
   The server generated these startup warnings when booting
   2025-03-26T03:56:00.593Z: Powered by FerretDB v2.0.0 and DocumentDB 0.102.0 (PostgreSQL 17.4).
   2025-03-26T03:56:00.593Z: Please star 🌟 us on GitHub: https://github.com/FerretDB/FerretDB and https://github.com/microsoft/documentdb.
   2025-03-26T03:56:00.593Z: The telemetry state is undecided. Read more about FerretDB telemetry and how to opt out at https://beacon.ferretdb.com.
------

postgres>
```
