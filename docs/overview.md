### Topics to read through

- [Frappe Devcontainer](https://github.com/frappe/frappe_docker/blob/main/docs/development.md#setup-bench--new-site-using-script)
- [Container Basics](https://discuss.frappe.io/t/container-basics/99306)
- [Build Production Containers with custom apps](https://github.com/frappe/frappe_docker/blob/main/docs/custom-apps.md)
- [Understand Frappe Production Containers](https://github.com/frappe/frappe_docker/blob/main/docs/single-compose-setup.md)
- [Container Builds](https://discuss.frappe.io/t/container-builds/99916)

### Clone frappe_docker

```shell
git clone https://github.com/frappe/frappe_docker buildwithhussain
cd buildwithhussain
```

### Development

```shell
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode
code .
```

Snippet for mailhog

```yaml
  # Mock SMTP
  mailhog:
    image: mailhog/mailhog:v1.0.1
    environment:
      - MH_STORAGE=maildir
    volumes:
      - mailhog-data:/maildir
    ports:
      - 1025:1025
      - 8025:8025

...
volumes:
  ...
  mailhog-data:
```

Reopen in devcontainer

```shell
code apps.json
```

Add following to `apps.json`:

```json
[
  {
    "url": "https://github.com/frappe/gameplan",
    "branch": "main"
  }
]
```

```shell
./installer.py -t develop -p 3.11.4 -n v18 -j apps.json -v

cp ~/.u2net/u2net.onnx /workspace/development
cd frappe-bench
nvm use v18
bench start
```

Note: change bench serve command for develop branch in Procfile to `bench serve --host=0.0.0.0 --port=8000`.

### Production

Reopen locally.

Add following in `images/custom/Containerfile`

```Dockerfile
COPY --chown=frappe:frappe ./development/u2net.onnx /home/frappe/.u2net/u2net.onnx
```

```shell
export APPS_JSON_BASE64=$(base64 -w 0 ./development/apps.json)
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=develop \
  --build-arg=PYTHON_VERSION=3.11.4 \
  --build-arg=NODE_VERSION=18.17.1 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=registry.gitlab.com/castlecraft/cepl-erpnext-images/gameplan:latest \
  --file=images/custom/Containerfile .
```

Push image

```shell
docker push registry.gitlab.com/castlecraft/cepl-erpnext-images/gameplan:latest
```

### Try image

Replace image and erpnext install command in `pwd.yml`.

```shell
sed -i 's|frappe/erpnext:v14.39.0|registry.gitlab.com/castlecraft/cepl-erpnext-images/gameplan:latest|g' pwd.yml
sed -i 's|--install-app erpnext|--install-app gameplan|g' pwd.yml
```

Start services

```shell
docker compose -p gameplan -f pwd.yml up -d
```

Check site logs

```shell
docker logs gameplan-create-site-1 -f
```

Open site `http://localhost:8080`
