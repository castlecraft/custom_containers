# Create Traefik LoadBalancer Service

```shell
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm install --namespace traefik --create-namespace traefik traefik/traefik
```

For Internal LB add appropriate annotation as per your cloud provider. e.g. Digitalocean:

```shell
helm upgrade --install --namespace traefik --create-namespace --set service.annotations."service\.beta\.kubernetes\.io/do-loadbalancer-network"="INTERNAL" traefik traefik/traefik
```

# Create kubernetes/ingress-nginx LoadBalancer Service

```shell
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

For Internal LB add appropriate annotation as per your cloud provider. e.g. Digitalocean:

```shell
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/do-loadbalancer-network"="INTERNAL"
```

Reference:

- https://github.com/traefik/traefik-helm-chart/blob/master/traefik/values.yaml
- https://kubernetes.github.io/ingress-nginx/deploy/#quick-start
- https://docs.digitalocean.com/products/kubernetes/how-to/configure-load-balancers/#internal-load-balancer
