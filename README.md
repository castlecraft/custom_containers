### Introduction

- This repo is based on official frappe_docker documentation to build [custom apps](https://github.com/frappe/frappe_docker/blob/main/custom_app/README.md).
- Fork this repo to build your own image with ERPNext and list of custom Frappe apps.
- Change the `frappe` and `erpnext` versions in `base_versions.json` to use them as base. These values correspond to tags and branch names on the github frappe and erpnext repo. e.g. `version-14`, `v14.18.1`
- Change `ci/clone-apps.sh` script to clone your private and public apps. Read comments in the file to update it as per need. This repo will install following apps:
  - https://github.com/castlecraft/cfe
  - https://github.com/castlecraft/microsoft_integration
- Change `images/backend.Dockerfile` to copy and install required apps with `install-app`.
- Change `images/frontend.Dockerfile` to install ERPNext if required.
- Change `docker-bake.hcl` for builds as per need.
- Workflows from `.github/workflows` will build latest or tagged images using GitHub. Change as per need.
- Runner will build images automatically and publish to container registry.
- Use `gitlab-ci.yml` in case of Gitlab CI.

### Manually Build images

Execute from root of app repo

Clone,

```shell
./ci/clone-apps.sh
```

Set environment variables,

- `FRAPPE_VERSION` set to use frappe version during building images. Default is `version-14`.
- `ERPNEXT_VERSION` set to use erpnext version during building images. Default is `version-14`.
- `VERSION` set the tag version. Default is `latest`.
- `REGISTRY_NAME` set the registry name. Default is `custom_app`.
- `BACKEND_IMAGE_NAME` set worker image name. Default is `custom_worker`.
- `FRONTEND_IMAGE_NAME` set nginx image name. Default is `custom_nginx`.

Build,

```shell
docker buildx bake -f docker-bake.hcl --load
```

Note:

- Use `docker buildx bake --load` to load images for usage with docker.
- Use `docker buildx bake --push` to push images to registry.
- Use `docker buildx bake --help` for more information.
- Change version in `version.txt` to build tagged images from the changed version.

### Development

Refer development directory to [start development](development/README.md)

### K8s Bench

Refer docs directory to use [Kubernetes Bench Operator](docs/k8s-bench.md)
