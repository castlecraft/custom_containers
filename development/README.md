## Prerequisites

- Install docker and docker compose cli plugin
- Add SSH keys to git for easy access to repo
- Copy `devcontainer` directory to `.devcontainer`.
- Copy `development/vscode-example` to `development/.vscode`.

## Setup

```shell
./setup.sh
cd frappe-bench
bench start
```

Open: `http://custom.localhost:8000`

Note: Add list of sites to `frappe` container's `extra_hosts` of `/workspace/.devcontainer/compose.yml`
