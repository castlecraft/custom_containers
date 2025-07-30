# Start from python:2.7-stretch as requested
FROM python:2.7-stretch AS base

# Add non-root user without password
RUN useradd -ms /bin/bash frappe

ARG GIT_REPO=https://github.com/frappe/frappe
ARG GIT_BRANCH=v10.x.x
ARG ARCH=amd64
ENV PYTHONUNBUFFERED 1
ENV NVM_DIR=/home/frappe/.nvm
ARG NODE_VERSION=6.11.4
ENV PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

# --- IMPORTANT: Configure apt for Debian Stretch Archive (absolutely minimal sources) ---
# Removed stretch-updates, stretch-backports, and debian-security as they are causing 404s.
# We are now relying solely on the 'main' archive for stretch.
RUN echo "deb http://archive.debian.org/debian stretch main" > /etc/apt/sources.list

# --- Install system dependencies ---
# Relying on 'main' archive for these packages. Removed problematic ones previously identified.
# If wkhtmltopdf from repo still fails, it may need to be removed completely or sourced differently.
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y --allow-unauthenticated \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    git \
    wget \
    curl \
    file \
    gpg \
    mariadb-client \
    postgresql-client \
    libssl-dev \
    libxml2 \
    libffi-dev \
    libpq-dev \
    # Weasyprint dependencies (These should still be in 'main')
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libjpeg62-turbo \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    gcc \
    make \
    libc6-dev \
    nano \
    fontconfig \
    nginx-light \
    gettext \
    wkhtmltopdf \
    jq \
    && rm -rf /var/lib/apt/lists/*

# --- SSL verification and initial pip setup ---
# NOTE: This block is still run as root by default from the base image setup.
# The pip install commands here are installing to /usr/local/lib/python2.7/site-packages
# This is fine for general tools like setuptools, wheel, pip, virtualenv.
RUN set -ex \
    && python -c "import ssl; import _ssl; print('SSL and _ssl modules loaded successfully!');" \
    && python -c "import ssl; print('Python SSL version: ' + ssl.OPENSSL_VERSION);" \
    && python -c "import urllib2; print(urllib2.urlopen('https://www.google.com').read()[:100]);" \
    && curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py \
    && python get-pip.py \
    && rm get-pip.py \
    # Install core tools globally as root.
    && python -m pip install --upgrade setuptools==44.0.0 wheel pip==9.0.3 virtualenv

# --- Copy common resources before adding 'frappe' user (if any are needed by root) ---
COPY resources/nginx-template.conf /templates/nginx/frappe.conf.template
COPY resources/nginx-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh

# --- User setup and Node.js (NVM) installation, Nginx config ---
ARG WKHTMLTOPDF_VERSION=0.12.6.1-3 # This arg is now effectively unused for installation but kept for reference
ARG WKHTMLTOPDF_DISTRO=stretch # This arg is now effectively unused for installation but kept for reference

RUN set -ex \
    # NodeJS - nvm installation requires bash
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    # Ensure nvm is sourced for future interactive shells
    && echo 'export NVM_DIR="/home/frappe/.nvm"' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion' >>/home/frappe/.bashrc \
    \
    # Nginx configuration
    && rm -fr /etc/nginx/sites-enabled/default \
    && sed -i '/user www-data/d' /etc/nginx/nginx.conf \
    && ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log \
    && touch /run/nginx.pid \
    && chown -R frappe:frappe /etc/nginx/conf.d \
    && chown -R frappe:frappe /etc/nginx/nginx.conf \
    && chown -R frappe:frappe /var/log/nginx \
    && chown -R frappe:frappe /var/lib/nginx \
    && chown -R frappe:frappe /run/nginx.pid \
    && chmod 755 /usr/local/bin/nginx-entrypoint.sh \
    && chmod 644 /templates/nginx/frappe.conf.template \
    \
    # Final cleanup of apt lists
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

# Ensure build dependencies for Python packages are available in this stage
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y --allow-unauthenticated \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    libpq-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    redis-tools \
    rlwrap \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Explicitly create the frappe-bench directory and set ownership BEFORE switching user
RUN mkdir -p /home/frappe/frappe-bench && chown frappe:frappe /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

USER frappe

# Add the user's local bin directory to PATH for this and subsequent RUN commands
ENV PATH="/home/frappe/.local/bin:${PATH}"

# Install honcho explicitly to a compatible version before bench
RUN pip install --user honcho==1.0.1

# Then install bench
RUN pip install --user git+https://github.com/revant/bench.git@mar-31-18#egg=frappe-bench

ARG APPS_JSON_BASE64
ARG FRAPPE_BRANCH=v10.1.13
ARG FRAPPE_PATH=https://github.com/frappe/frappe

# --- Copy the patched setup.py file ---
# This must be copied BEFORE the main RUN block where Frappe is installed.
# It will be applied after bench init clones the Frappe repo.
COPY resources/frappe_setup.py /tmp/frappe_setup.py
COPY resources/frappe_requirements.txt /tmp/frappe_requirements.txt

# --- Core Bench Initialization and App Installation Logic ---
RUN \
  # 1. Run bench init to set up the basic environment, create venv, and clone Frappe.
  #    It will likely fail during Frappe's installation due to pip.req, but that's okay.
  bench init --ignore-exist /home/frappe/frappe-bench \
    --no-procfile \
    --no-backups \
    --skip-redis-config-generation \
    --verbose \
    --frappe-branch=${FRAPPE_BRANCH} \
    --frappe-path=${FRAPPE_PATH} \
    --python=/usr/local/bin/python || true && \
  \
  # 2. Overwrite Frappe's setup.py with our pre-patched version.
  #    This must be done AFTER Frappe is cloned into apps/frappe by bench init.
  cp /tmp/frappe_setup.py /home/frappe/frappe-bench/apps/frappe/setup.py && \
  cp /tmp/frappe_requirements.txt /home/frappe/frappe-bench/apps/frappe/requirements.txt && \
  \
  # 3. Activate the virtual environment and manually install Frappe.
  #    This uses the patched setup.py, so it should now succeed.
  . /home/frappe/frappe-bench/env/bin/activate && \
  pip install --upgrade setuptools==44.0.0 wheel pip==9.0.3 && \
  pip install -e /home/frappe/frappe-bench/apps/frappe --no-cache-dir && \
  \
  # 4. Handle additional apps from APPS_JSON_BASE64 (if provided).
  if [ -n "${APPS_JSON_BASE64}" ]; then \
    mkdir -p /opt/frappe && echo "${APPS_JSON_BASE64}" | base64 -d > /opt/frappe/apps.json; \
    jq -r '.[] | .name + " " + .url + " --branch " + .branch' /opt/frappe/apps.json | while read -r app_name app_url app_branch; do \
      bench get-app "$app_url" --branch "$app_branch" --name "$app_name" --verbose && \
      bench install-app "$app_name" --verbose; \
    done; \
  fi && \
  \
  # 5. Continue with existing post-init steps for bench configuration and cleanup.
  cd /home/frappe/frappe-bench && \
  echo "{}" > sites/common_site_config.json && \
  find apps -mindepth 1 -path "*/.git" | xargs rm -fr

FROM base AS backend

USER frappe

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

VOLUME [ \
  "/home/frappe/frappe-bench/sites", \
  "/home/frappe/frappe-bench/sites/assets", \
  "/home/frappe/frappe-bench/logs" \
]

CMD [ \
  "/home/frappe/frappe-bench/env/bin/gunicorn", \
  "--chdir=/home/frappe/frappe-bench/sites", \
  "--bind=0.0.0.0:8000", \
  "--threads=4", \
  "--workers=2", \
  "--worker-class=gthread", \
  "--worker-tmp-dir=/dev/shm", \
  "--timeout=120", \
  "--preload", \
  "frappe.app:application" \
]
