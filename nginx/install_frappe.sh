#!/bin/bash

FRAPPE_BRANCH=${1}

[ "${FRAPPE_BRANCH}" ] && FRAMEWORK_BRANCH="-b ${FRAPPE_BRANCH}"

mkdir -p /home/frappe/frappe-bench/sites/assets
cd /home/frappe/frappe-bench
mkdir -p apps
cd apps
git clone --depth 1 https://github.com/frappe/frappe frappe ${FRAMEWORK_BRANCH}

echo -e "frappe" > /home/frappe/frappe-bench/sites/apps.txt

cd /home/frappe/frappe-bench/apps/frappe && yarn
yarn production

echo "rsync -a --delete /var/www/html/assets/frappe /assets" > /rsync
