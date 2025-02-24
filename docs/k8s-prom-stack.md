# Install Kube Prometheus Stack Helm Chart

```shell
helm upgrade --install --namespace=monitoring --create-namespace k8s-prom-stack  prometheus-community/kube-prometheus-stack
```

Note: If you face [issue](https://github.com/prometheus-community/helm-charts/issues/467#issuecomment-957091174) with prometheus-node-exporter.

```shell
kubectl -n monitoring patch ds k8s-prom-stack-prometheus-node-exporter --type "json" -p '[{"op": "remove", "path" : "/spec/template/spec/containers/0/volumeMounts/2/mountPropagation"}]'
```
