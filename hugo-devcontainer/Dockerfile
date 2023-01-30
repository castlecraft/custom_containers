FROM debian:bullseye-slim
# This Dockerfile adds a non-root user with sudo access. Use the "remoteUser"
# property in devcontainer.json to use it. On Linux, the container user's GID/UIDs
# will be updated to match your local UID/GID (when using the dockerFile property).
# See https://aka.ms/vscode-remote/containers/non-root-user for details.
ARG USERNAME=hugo
ARG GROUPNAME=$USERNAME
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ENV DEBIAN_FRONTEND=noninteractive

RUN groupadd -g ${USER_GID} ${USERNAME} && \
    useradd --no-log-init -r -m -u ${USER_UID} -g ${USER_GID} -G sudo ${USERNAME} -s /bin/zsh && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Install Dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    gnupg2 \
    zsh \
    git \
    vim \
    curl \
    wget

# Install caddy
RUN curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg && \
    curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt | tee /etc/apt/sources.list.d/caddy-stable.list && \
    apt-get update && apt-get install -y caddy

# Install Hugo
RUN cd /tmp/ && \
    curl -s https://api.github.com/repos/gohugoio/hugo/releases/latest \
    | grep "browser_download_url.*hugo_extended.*_Linux-64bit\.tar\.gz" \
    | cut -d ":" -f 2,3 \
    | tr -d '"' \
    | wget -qi - && \
    tar -xzf $(find . -name "*Linux-64bit.tar.gz") && \
    chmod 755 hugo && mv hugo /usr/local/bin/ && \
    cd -

USER $USERNAME

RUN curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh | sh
