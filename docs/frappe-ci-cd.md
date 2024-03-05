### Setup development environment

- Use VS Code devcontainer. It needs a `.devcontainer` directory in your VS Code project directory to start development using containers. Create a repo for your developers to bootstrap development environment using devcontainer. Add additional scripts to do chores.
- Basic devcontainer setup for frappe exists in `devcontainer` directory
- Container can be customized with custom image and additional dependencies installed as part of initialization.
- Refer other frappe example located under `kube-devcontainer` to build custom image using `Dockerfile`, `devcontainer.json` and `compose.yml`
- Other devcontainer examples are `dind-devcontainer` to try docker in docker and `hugo-devcontainer` to develop static site using hugo.

### Use pre-commit for code lint and format

Install pre-commit using pip.

Place example file `frappe-ci-cd/.pre-commit-config.yaml` at root of your repo.

Make changes to config file as per need.

Current pre-commit requires `.eslintrc.js` and `.prettierrc` files to configure the checks. All example files are available under `frappe-ci-cd` directory.

Following example for `python:3-alpine` image used in CI task. Working directory is your root of your app repo.

```shell
# Install dependencies
apk add -U git nodejs gcc musl-dev

# Create py env
python3 -m venv env

# Upgrade pip
./env/bin/pip install -U pip

# Install pre-commit
./env/bin/pip install pre-commit

# execute pre-commit run
./env/bin/pre-commit run --color=always --all-files
```

### Use frappe/bench container image to test app.

Sample compose.yaml for running tests are placed under `frappe-ci-cd/frappe-tests.yaml`. Change the `command` for `tests` service.

Execute following command to run tests:

```shell
# Create and start services
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml create
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml start mariadb
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml start redis-cache
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml start redis-queue
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml start redis-socketio

# Run tests
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml run tests

# Stop services
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml stop

# Clean up
docker compose -p frappe-tests -f frappe-ci-cd/frappe-tests.yaml rm -f
docker volume prune -f
docker network prune -f
```

### Release individual app

Sample release script is under `frappe-ci-cd/release.py`. Place it in the root of your repo and execute to create release. It needs `GitPython` and `semantic-version` present under environment.

The release script bumps up the `__version__` string in `__init__.py`, adds git tag and `git push` with tags on specified `--remote` branch. If remote is not specified it will read remote from git and provide selection for user to input remote. Pass `--remote` in case of unattended execution.

```shell
# Create py env
python3 -m venv env

# Upgrade pip
./env/bin/pip install -U pip

# Install GitPython
./env/bin/pip install GitPython

# Install semantic-version
./env/bin/pip install semantic-version

./env/bin/python release.py --help

usage: release.py [-h] [-d] [-j | -n | -p]

optional arguments:
  -h, --help            show this help message and exit
  -d, --dry-run         DO NOT make changes
  -r REMOTE, --remote REMOTE
                        git remote to push release on
  -j, --major           Release Major Version
  -n, --minor           Release Minor Version
  -p, --patch           Release Patch Version
```

### Frappe apps builder-repo

Following commands will use python script `frappe-builder-repo/generate_apps_json.py` to render `apps.json` from directory mentioned in `$APPS_JSONS` environment variable or defaults to directory called `benches`.

Sample `apps.json` Jinja2 template found here `frappe-builder-repo/apps.json`

Copy all files from `frappe-builder-repo` to root of your "builder-repo"

Execute following to build image from root of your builder repo

```shell
python -m venv env
. ./env/bin/activate
pip install -U pip Jinja2
source ./common.env
export REPO_PAT=revant
export APPS_JSON_BASE64=$(python generate_apps_json.py -t apps.json | base64 -w 0)
docker build \
  --build-arg=FRAPPE_PATH=${FRAPPE_PATH} \
  --build-arg=FRAPPE_BRANCH=${FRAPPE_BRANCH} \
  --build-arg=PYTHON_VERSION=${PYTHON_VERSION} \
  --build-arg=NODE_VERSION=${NODE_VERSION} \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=ghcr.io/org/repo/image:1.0.0 \
  --file=Containerfile .
```

You can customize the `Containerfile`. You can copy additional files by placing the under `resources` directory and specifying `COPY` in `Containerfile`.
