## Prerequisites

- Install docker and docker compose cli plugin
- Add SSH keys to git for easy access to repo
- Copy `devcontainer` directory to `.devcontainer`.
- Copy `development/vscode-example` to `development/.vscode`.

## Setup

Reopen in VS Code devcontainer, enter the `frappe` container.

For non VS Code development start containers with:

```shell
docker compose -p custom_bench -f .devcontainer/compose.yml up -d
```

Enter development container with:

```shell
docker compose -p custom_bench exec -e "TERM=xterm-256color" -it frappe bash
```

Once in `frappe` container execute:

```shell
./setup.sh
cd frappe-bench
bench start
```

Open: `http://custom.localhost:8000`

If not using VS Code open `development` or `development/frappe-bench` directory from this repo in your editor.

Note: Add list of sites to `frappe` container's `extra_hosts` in `.devcontainer/compose.yml` for sites from same container to communicate with each other by using site name.

## Changes for private apps

- Use ssh uri instead of https for app repo on `apps.json`
- Setup ssh keys for git access on host machine. `compose.yml` mounts `${HOME}/.ssh` in container at `/home/frappe/.ssh`.
