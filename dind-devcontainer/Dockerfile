FROM frappe/bench:latest

# Install Docker
RUN sudo apt-get update && sudo apt-get install -y jq httpie && \
  curl -fsSL https://get.docker.com | sudo bash

ENV DOCKER_HOST=docker
