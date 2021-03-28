#!/bin/bash

APP_NAME=${1}
APP_REPO=${2}
APP_BRANCH=${3}

[ "${APP_BRANCH}" ] && BRANCH="-b ${APP_BRANCH}"

echo -e "frappe\n${APP_NAME}" > /home/frappe/frappe-bench/sites/apps.txt
cd /home/frappe/frappe-bench/apps
git clone --depth 1 ${APP_REPO} ${APP_NAME} ${BRANCH}
cd /home/frappe/frappe-bench/apps/${APP_NAME} && yarn

cd /home/frappe/frappe-bench/apps/frappe
yarn production --skip_frappe --app ${APP_NAME}

mkdir -p /home/frappe/frappe-bench/sites/assets/${APP_NAME}
cp -R /home/frappe/frappe-bench/apps/${APP_NAME}/${APP_NAME}/public/* /home/frappe/frappe-bench/sites/assets/${APP_NAME} 2>/dev/null || :
cp -R /home/frappe/frappe-bench/apps/${APP_NAME}/node_modules /home/frappe/frappe-bench/sites/assets/${APP_NAME}/ 2>/dev/null || :

echo "rsync -a --delete /var/www/html/assets/${APP_NAME} /assets" >> /rsync
chmod +x /rsync
