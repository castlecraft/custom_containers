FROM frappe/bench:latest

COPY entrypoint.sh /entrypoint.sh

# Install Tools
RUN sudo apt-get update && sudo apt-get install -y jq wait-for-it zsh && \
    sudo curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | sudo bash && \
    curl -fsSL https://fluxcd.io/install.sh | sudo bash && \
    curl -fsSL https://get.docker.com | sudo bash && \
    mkdir -p /home/frappe/.kube && \
    sudo chmod +x /entrypoint.sh

RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v1.1.5/zsh-in-docker.sh)" -- \
    -p git \
    -p kubectl \
    -p https://github.com/zsh-users/zsh-autosuggestions \
    -p https://github.com/zsh-users/zsh-completions

ENV DOCKER_HOST=docker
ENV KUBECONFIG=/home/frappe/.kube/config

ENTRYPOINT [ "/entrypoint.sh" ]
