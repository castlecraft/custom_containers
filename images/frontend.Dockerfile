ARG FRAPPE_VERSION
ARG ERPNEXT_VERSION
ARG PYTHON_VERSION

FROM frappe/bench:latest as assets

ARG NODE_VERSION
ENV NVM_DIR=/home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

ARG FRAPPE_VERSION
# Use 3.9.9 for version 13
ARG PYTHON_VERSION=3.10.5
RUN PYENV_VERSION=${PYTHON_VERSION} bench init --version=${FRAPPE_VERSION} --skip-redis-config-generation --verbose --skip-assets /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

# Uncomment following if ERPNext is required
# ARG ERPNEXT_VERSION
# RUN bench get-app --branch=${ERPNEXT_VERSION} --skip-assets --resolve-deps erpnext

COPY --chown=frappe:frappe repos apps

RUN bench setup requirements

RUN export BUILD_OPTS="--production --hard-link" && \
  if [ -z "${FRAPPE_BRANCH##*v12*}" ] || [ -z "${FRAPPE_BRANCH##*v13*}" ] \
    || [ "$FRAPPE_BRANCH" = "version-12" ] || [ "$FRAPPE_BRANCH" = "version-13" ]; then \
    export BUILD_OPTS="--make-copy"; \
  fi && \
  FRAPPE_ENV=production bench build --verbose ${BUILD_OPTS}

FROM frappe/frappe-nginx:${FRAPPE_VERSION}

USER root

RUN rm -fr /usr/share/nginx/html/assets

COPY --from=assets /home/frappe/frappe-bench/sites/assets /usr/share/nginx/html/assets

USER 1000
