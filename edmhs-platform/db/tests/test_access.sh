#!/usr/bin/env bash
# Role-isolation tests for the EDMHS schema. Usage: PGHOST=... PGPORT=... PGUSER=postgres db/tests/test_access.sh
set -euo pipefail
DB=${DB:-edmhs_test}; D=$(dirname "$0")/../init
# Test-only password for the demo login roles (servers that require password auth, e.g. CI).
TEST_PW=${TEST_ROLE_PASSWORD:-test-only}
psql -qc "DROP DATABASE IF EXISTS $DB" && psql -qc "CREATE DATABASE $DB"
psql -d $DB -v ON_ERROR_STOP=1 -q -f $D/001_schema.sql -f $D/002_seed.sql -f $D/../dev/010_synthetic_participants.sql
psql -d $DB -q <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='fac_demo') THEN CREATE ROLE fac_demo LOGIN PASSWORD '$TEST_PW' IN ROLE edm_facilitator; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='ana_demo') THEN CREATE ROLE ana_demo LOGIN PASSWORD '$TEST_PW' IN ROLE edm_analyst; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='clin_demo') THEN CREATE ROLE clin_demo LOGIN PASSWORD '$TEST_PW' IN ROLE edm_clinician; END IF;
END \$\$;
ALTER ROLE fac_demo PASSWORD '$TEST_PW'; ALTER ROLE ana_demo PASSWORD '$TEST_PW'; ALTER ROLE clin_demo PASSWORD '$TEST_PW';
INSERT INTO core.staff(db_role, full_name, app_role) VALUES ('fac_other','Other Facilitator','facilitator');
UPDATE intake.cohort SET facilitator=(SELECT staff_id FROM core.staff WHERE db_role='fac_other') WHERE dev_band IN ('15-17','18-24');
SQL
fail=0
expect(){ local who=$1 sql=$2 want=$3; got=$(PGPASSWORD="$([ "$who" = postgres ] && echo "${PGPASSWORD:-}" || echo "$TEST_PW")" psql -U "$who" -d $DB -tAc "$sql" 2>&1 | head -1 || true)
  if [[ "$want" =~ ^[0-9]+$ && "$got" == "$want" ]] || [[ ! "$want" =~ ^[0-9]+$ && "$got" == *"$want"* ]]; then echo "PASS $who: $sql"; else echo "FAIL $who: $sql -> $got (want $want)"; fail=1; fi; }
expect postgres  "select count(*) from intake.participant" 24
expect fac_demo  "select count(*) from intake.participant" 9
expect fac_demo  "select phone_enc from intake.participant" "permission denied"
expect clin_demo "select count(*) from intake.participant" 0
expect ana_demo  "select count(*) from intake.participant" "permission denied"
expect ana_demo  "select * from core.secret" "permission denied"
expect ana_demo  "select count(distinct rid) from analytics.participant_deid" 24
expect ana_demo  "select count(*) from analytics.participant_deid where age_at_enroll not between 10 and 24" 0
exit $fail
