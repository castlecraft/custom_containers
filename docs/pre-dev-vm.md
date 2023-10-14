# Use portainer and code-server

```shell
docker compose -p portainer -f pre-dev-vm/portainer.yml up -d
```

## Add pre-dev-bench stack

Stacks > Add,  refer yaml from `pre-dev-vm/pre-dev-bench.yml`.

## Start container with commands:

```shell
docker run --rm -it \
  -v /opt/benches:/home/frappe/benches \
  -w /home/frappe/benches \
  --network pre-dev-bench_default \
  frappe/bench:latest \
  bash -c "sudo chown -R frappe:frappe . && wget https://raw.githubusercontent.com/frappe/frappe_docker/main/development/installer.py && chmod +x installer.py && echo '[]' > apps-example.json && ./installer.py"
```

## Open VS Code in browser

Open `http://vm-ip-addr:8443` in browser to access VS Code through code-server.

## Restart pre-dev-bench-frappe

Stacks > Select "pre-dev-bench" > Select service "pre-dev-bench-frappe-1" > Restart

# Use VS Code Devcontainer with VS Code Remote SSH Extension

- Create a VM for development and configure SSH access with passwordless key.
- [Install docker](docker-swarm.md#install-prerequisites)
- Open Remote, and clone https://github.com/frappe/frappe_docker at location `/home/ubuntu/frappe_docker`
- Open remote directory in VS Code
- Copy `devcontainer-example` to `.devcontainer` directory.
- Reopen in Devcontainer.

Above steps can use remote machine as docker host for devcontainer setup.

More about the setup: https://code.visualstudio.com/remote/advancedcontainers/develop-remote-host#_connect-using-the-remote-ssh-extension-recommended
