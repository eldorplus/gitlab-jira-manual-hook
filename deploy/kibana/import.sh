#!/usr/bin/env sh
set -eu

KIBANA_URL="${KIBANA_URL:?KIBANA_URL is required}"
KIBANA_API_KEY="${KIBANA_API_KEY:?KIBANA_API_KEY is required}"

curl --fail --silent --show-error \
  -X POST "${KIBANA_URL%/}/api/saved_objects/_import?overwrite=true" \
  -H "Authorization: ApiKey ${KIBANA_API_KEY}" \
  -H 'kbn-xsrf: true' \
  -H 'Content-Type: multipart/form-data' \
  -F file=@gitlab-pipelines.ndjson

echo "Kibana assets imported successfully."
