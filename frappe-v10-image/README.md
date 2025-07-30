Execute Commands:

```shell
export APPS_JSON='[{"url": "https://github.com/frappe/erpnext","branch": "v10.1.15"}]'
export APPS_JSON_BASE64=$(echo $APPS_JSON|base64)
docker build --progress=plain \
  --build-arg=FRAPPE_BRANCH=v10.1.13 \
  --build-arg=APPS_JSON_BASE64=${APPS_JSON_BASE64} \
  --tag=fv10:latest \
  --file=image/v10.Containerfile image
```
