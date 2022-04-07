### Introduction

- This repo is based on official frappe_docker documentation to build custom apps.
- Fork this repo to build your own image with ERPNext and list of custom Frappe apps.
- Change `ci/clone-apps.sh` script to clone your private and public apps. This repo will install following apps:
  - https://github.com/yrestom/POS-Awesome
  - https://github.com/zerodha/frappe-attachments-s3
  - https://github.com/pipech/frappe-metabase
  - https://github.com/franknyarkoh/bookings
  - https://github.com/frappe/bench_manager
- Change `images/backend.Dockerfile` to copy and install required apps with `install-app`.
- Change `images/frontend.Dockerfile` to copy and install required apps `install-app`.
- Change `docker-bake.hcl` for builds as per need.
- Workflows from `.github/workflows` will build latest or tagged images. Change as per need.
- Registry will build images automatically and publish to github container registry.

### Manually Build images

Execute from root of app repo

Clone,

```shell
./ci/clone-apps.sh
```

Set environment variables,

- `FRAPPE_VERSION` set to use frappe version during building images. Default is `version-13`.
- `ERPNEXT_VERSION` set to use erpnext version during building images. Default is `version-13`.
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
