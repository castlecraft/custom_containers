FROM frappe/bench:latest

COPY entrypoint.sh /entrypoint.sh

# Install Tools
RUN sudo curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | sudo bash && \
    curl -fsSL https://fluxcd.io/install.sh | sudo bash && \
    curl -fsSL https://get.docker.com | sudo bash && \
    mkdir -p /home/frappe/.kube && \
    sudo chmod +x /entrypoint.sh

ENV DOCKER_HOST=docker
ENV KUBECONFIG=/home/frappe/.kube/config

ENTRYPOINT [ "/entrypoint.sh" ]
