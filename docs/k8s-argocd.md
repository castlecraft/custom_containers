# Install ArgoCD Helm Chart

```shell
helm repo add argo https://argoproj.github.io/argo-helm
```

Customize `values.yaml`, example using traefik.

```yaml
global:
  domain: "argocd.localhost"

configs:
  params:
    server.insecure: true

server:
  ingress:
    enabled: true
    annotations:
      # nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
      # nginx.ingress.kubernetes.io/ssl-passthrough: "true"
      kubernetes.io/ingress.class: traefik
      cert-manager.io/cluster-issuer: cybertec-at-le-issuer
      traefik.ingress.kubernetes.io/sslPassthrough: "true"
    ingressClassName: "traefik"
    # ingressClassName: "nginx"
```

Create helm release

```shell
helm upgrade --install --namespace=argocd --create-namespace argocd argo/argo-cd -f values.yaml
```
