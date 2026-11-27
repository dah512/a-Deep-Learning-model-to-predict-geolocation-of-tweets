#!/bin/sh
# Runs once on the postgres container's first start (docker-entrypoint-initdb.d).
# Creates the API login roles from env secrets, each bound to a least-privileged group role.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE ROLE ict_api LOGIN PASSWORD '${INTAKE_DB_PASSWORD}' IN ROLE edm_intake;
CREATE ROLE ana_api LOGIN PASSWORD '${ANALYTICS_DB_PASSWORD}' IN ROLE edm_analyst;
SQL
