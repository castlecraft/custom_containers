## Gitlab

```yaml
stages:
  - build

build_version:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  only:
    refs:
      - main
  script:
    - |
      mkdir -p /kaniko/.docker
      export BASIC_AUTH=$(echo -n ${CI_REGISTRY_USER}:${CI_JOB_TOKEN} | base64)
      echo "{
        \"auths\": {
          \"${CI_REGISTRY:-registry.gitlab.com}\":{
            \"auth\": \"${BASIC_AUTH}\"
            }
          }
        }" > /kaniko/.docker/config.json
      /kaniko/executor \
        --dockerfile=images/custom/Containerfile \
        --context=${BUILD_CONTEXT:-git://github.com/frappe/frappe_docker} \
        --build-arg=FRAPPE_PATH=${FRAPPE_PATH:-https://github.com/frappe/frappe} \
        --build-arg=FRAPPE_BRANCH=${FRAPPE_BRANCH:-v14.23.0} \
        --build-arg=PYTHON_VERSION=${PYTHON_VERSION:-3.10.5} \
        --build-arg=NODE_VERSION=${NODE_VERSION:-16.18.0} \
        --build-arg=APPS_JSON_BASE64=${APPS_JSON_BASE64:-$(base64 -w 0 apps.json)} \
        --destination=${IMAGE_NAME:-registry.gitlab.com/castlecraft/cepl-erpnext-images/apps:${VERSION:-$(cat version.txt)}} \
        --cache=true
```

#### Variables Used

- `VERSION`, set it for the tag version of image to be built and pushed, default reads from version.txt file from repo.
- `CI_REGISTRY_USER`, set it to the container registry user
- `CI_JOB_TOKEN`, set it to the container registry password
- `CI_REGISTRY`, set it to the container registry url. (compatible with docker hub)
- `BUILD_CONTEXT`, set it to the kaniko build context, default: `git://github.com/frappe/frappe_docker`
- `FRAPPE_PATH`, set it to the frappe repo url, default `https://github.com/frappe/frappe`
- `FRAPPE_BRANCH`, set it to the frappe repo branch, default `v14.23.0`
- `PYTHON_VERSION`, set it to python version to be used, default `3.10.5`
- `NODE_VERSION`, set it to nodejs version to be used, default `16.18.0`
- `APPS_JSON_BASE64`, set it to base64 encoded apps.json, default apps.json from repo will be used.
- `IMAGE_NAME`, set it to image name without the tag. default `registry.gitlab.com/castlecraft/cepl-erpnext-images/apps`

#### Curl command

```shell
curl -X POST \
    --fail \
    -F token=$TOKEN \
    -F "ref=$REF_NAME" \
    -F "variables[VERSION]=nightly" \
    -F "variables[IMAGE_NAME]=registry.gitlab.com/orgname/project/image" \
    -F "variables[APPS_JSON_BASE64]=W3sidXJsIjoiaHR0cHM6Ly9naXRodWIuY29tL2ZyYXBwZS9wYXltZW50cyIsImJyYW5jaCI6ImRldmVsb3AifV0=" \
    https://gitlab.com/api/v4/projects/$PROJECT_ID/trigger/pipeline
```
