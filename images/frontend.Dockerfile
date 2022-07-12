# syntax=docker/dockerfile:1.3

ARG FRAPPE_VERSION
ARG ERPNEXT_VERSION

FROM frappe/assets-builder:${FRAPPE_VERSION} as assets

COPY repos apps

RUN install-app posawesome && \
    install-app wiki

FROM frappe/erpnext-nginx:${ERPNEXT_VERSION}

COPY --from=assets /out /usr/share/nginx/html
