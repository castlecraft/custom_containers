#!/bin/bash

if [ ! -f "${KUBECONFIG}" ]; then
  curl -sSL k3s:8081>"${KUBECONFIG}"
fi

exec "$@"
