ARG FRAPPE_VERSION
ARG ERPNEXT_VERSION

FROM frappe/bench:latest as assets

ARG FRAPPE_VERSION
RUN bench init --version=${FRAPPE_VERSION} --skip-redis-config-generation --verbose --skip-assets /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

# Comment following if ERPNext not required
ARG ERPNEXT_VERSION
RUN bench get-app --branch=${ERPNEXT_VERSION} --skip-assets --resolve-deps erpnext

COPY --chown=frappe:frappe repos apps

RUN bench setup requirements

RUN bench build --production --verbose --hard-link

FROM frappe/frappe-nginx:${FRAPPE_VERSION}

USER root

RUN rm -fr /usr/share/nginx/html/assets

COPY --from=assets /home/frappe/frappe-bench/sites/assets /usr/share/nginx/html/assets

USER 1000
