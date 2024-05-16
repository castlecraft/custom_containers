FROM debian:bookworm-slim
# This Dockerfile adds a non-root user with sudo access. Use the "remoteUser"
# property in devcontainer.json to use it. On Linux, the container user's GID/UIDs
# will be updated to match your local UID/GID (when using the dockerFile property).
# See https://aka.ms/vscode-remote/containers/non-root-user for details.
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV NVM_DIR=/home/vscode/.nvm
ENV NODE_VERSION=20.13.1
ENV PATH="/home/vscode/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"

# Install sudo
RUN apt-get update && apt-get install -y \
  sudo \
  python3 \
  python3-requests \
  curl \
  git \
  procps \
  krb5-user \
  wait-for-it \
  wget \
  # Add user, group, and add user to sudoer group
  && groupadd --gid $USER_GID $USERNAME \
  && useradd --no-log-init -r -m -u $USER_UID -g $USER_GID -G sudo -s /bin/bash $USERNAME \
  && echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers \
  && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
  && apt-get install -y ./google-chrome-stable_current_amd64.deb \
  && rm ./google-chrome-stable_current_amd64.deb

USER $USERNAME

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash \
  && npm install lerna @nestjs/cli yarn @angular/cli -g

CMD [ "tail", "-f", "/dev/null" ]
