#!/bin/bash

# Create assets directory if not found
[ -d "/home/frappe/frappe-bench/sites/assets" ] || mkdir -p "/home/frappe/frappe-bench/sites/assets"

# Copy assets*.json from image to assets volume
# cp -uf /opt/frappe/assets/*.json "/home/frappe/frappe-bench/sites/assets/" 2>/dev/null
cp -f /opt/frappe/assets/*.json "/home/frappe/frappe-bench/sites/assets/" 2>/dev/null

# Symlink public directories of app(s) to assets
find /home/frappe/frappe-bench/apps -type d -name public | while read -r line; do
  app_name=$(echo "${line}" | awk -F / '{print $(NF-1)}')
  assets_source=${line}
  assets_dest=/home/frappe/frappe-bench/sites/assets/${app_name}
  # Create link if not found
  [ -L "${assets_dest}" ] || ln -sf "${assets_source}" "${assets_dest}";
done

exec "$@"
