#!/bin/bash

DOCKER_IP=$(ping -c 2 docker | awk -F '[()]' '/PING/ { print $2}')
export DOCKER_IP
DOCKER_PORT=2375
export DOCKER_PORT
DOCKER_API="${DOCKER_IP}:${DOCKER_PORT}"
export DOCKER_API
