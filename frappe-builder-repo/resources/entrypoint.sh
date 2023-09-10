#!/bin/bash

# Create assets directory if not found
[ -d "${PWD}/sites/assets" ] || mkdir -p "${PWD}/sites/assets"

# Copy assets*.json from image to assets volume if updated
cp -uf /opt/frappe/assets/*.json "${PWD}/sites/assets/" 2>/dev/null

# Symlink public directories of app(s) to assets
find apps -type d -name public | while read -r line; do
  app_name=$(echo "${line}" | awk -F / '{print $3}')
  assets_source=${PWD}/${line}
  assets_dest=${PWD}/sites/assets/${app_name}

  # Create symlink if not found
  [ -L "${assets_dest}" ] || ln -sf "${assets_source}" "${assets_dest}";
done

exec "$@"
