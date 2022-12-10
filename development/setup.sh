#!/bin/bash

# Initialize Bench
bench init \
  --frappe-branch=version-14 \
  --apps_path=apps.json \
  --skip-redis-config-generation \
  --verbose frappe-bench

# Change to frappe-bench
cd frappe-bench

# Set global bench configs
echo "Configuring Bench ..."
echo "Set db_host to mariadb"
bench set-config -g db_host mariadb
echo "Set redis_cache to redis://redis-cache:6379"
bench set-config -g redis_cache redis://redis-cache:6379
echo "Set redis_queue to redis://redis-queue:6379"
bench set-config -g redis_queue redis://redis-queue:6379
echo "Set redis_socketio to redis://redis-socketio:6379"
bench set-config -g redis_socketio redis://redis-socketio:6379

# Create custom.localhost site
echo "Create custom.localhost, install apps castlecraft, microsoft_integration"
bench new-site \
  --no-mariadb-socket \
  --db-root-password=123 \
  --admin-password=admin \
  --install-app=castlecraft \
  --install-app=microsoft_integration \
  custom.localhost
