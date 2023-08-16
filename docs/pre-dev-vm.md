## Start portainer

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

## Restart pre-dev-bench-frappe

Stacks > Select "pre-dev-bench" > Select service "pre-dev-bench-frappe-1" > Restart
