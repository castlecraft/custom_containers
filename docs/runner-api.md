## General Setup

- Default variables are taken from `ci/build.env` file if no input is provided.
- `ci/version.txt` stores the image version tag. Change the file to change the output tag. It can be overridden by job inputs.

## Gitlab

Check the `.gitlab-ci.yml` file.

Input Variables

- `CI_REGISTRY`, set it to the container registry url. (compatible with docker hub)
- `CI_PROJECT_NAMESPACE`, set it to the group name on gitlab
- `CI_PROJECT_NAME`, set it to the project name on gitlab
- `IMAGE_NAME`, set it to image name without the tag. default `registry.gitlab.com/castlecraft/cepl-erpnext-images/apps`
- `CI_REGISTRY_USER`, set it to the container registry user
- `CI_JOB_TOKEN`, set it to the container registry password
- `CONTAINERFILE`, set it to the Dockerfile path in kaniko context
- `BUILD_CONTEXT`, set it to the kaniko build context, default: `git://github.com/frappe/frappe_docker`
- `FRAPPE_PATH`, set it to the frappe repo url, default `https://github.com/frappe/frappe`
- `FRAPPE_BRANCH`, set it to the frappe repo branch, default `v14.23.0`
- `PYTHON_VERSION`, set it to python version to be used, default `3.10.5`
- `NODE_VERSION`, set it to nodejs version to be used, default `16.18.0`
- `APPS_JSON_BASE64`, set it to base64 encoded apps.json, default apps.json from repo will be used.
- `VERSION`, set it for the tag version of image to be built and pushed, default reads from version.txt file from repo.


Trigger using ReST API

```shell
curl -X POST \
  --fail \
  -F token=$TOKEN \
  -F "ref=$REF_NAME" \
  -F "variables[VERSION]=nightly" \
  -F "variables[IMAGE_NAME]=apps" \
  -F "variables[APPS_JSON_BASE64]=W3sidXJsIjoiaHR0cHM6Ly9naXRodWIuY29tL2ZyYXBwZS9wYXltZW50cyIsImJyYW5jaCI6ImRldmVsb3AifV0=" \
  https://gitlab.com/api/v4/projects/$PROJECT_ID/trigger/pipeline
```

## GitHub

Check the `.github/workflows/build.yaml`. Run the workflow on `main` or your repos default branch. It is set to `build` branch in example file.

Job Inputs

- `image`: Image name
- `version`: Image version tag
- `frappe-repo`: Frappe repo
- `frappe-version`: Frappe branch
- `py-version`: Python version
- `nodejs-version`: NodeJS version
- `apps-json-base64`: base64 encoded string of apps.json
- `context`: kaniko context
- `dockerfile`: dockerfile path from context
- `registry-user`: registry username

Trigger using ReST API

```shell
curl \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <YOUR-TOKEN>"\
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_ID}/dispatches \
  -d '{
    "ref": "topic-branch",
    "inputs": {
      "image": "apps",
      "apps-json-base64": "W3sidXJsIjoiaHR0cHM6Ly9naXRodWIuY29tL2ZyYXBwZS9wYXltZW50cyIsImJyYW5jaCI6ImRldmVsb3AifV0="
    }
  }'
```

## Practices

- `apps.json` may contain repo tokens for git https basic auth. You may commit them on private repos and make sure they are never made public.
- another alternative is to generate `apps.json` with CI secrets and then passing it to build arg. It can be done with `echo`, environment variables and shell pipes. Check how config.json is generated. It can be done as a step in job if it needs complex tools.
