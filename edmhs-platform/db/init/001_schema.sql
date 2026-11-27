-- EDMHS shared backend: ICT intake, KATA collaborative access, de-identified analytics, GPCS grants.
-- PostgreSQL 16. Run as a superuser on an empty database:  psql -v ON_ERROR_STOP=1 -f 001_schema.sql
--
-- Schemas
--   core      organizations, programs, staff, roles
--   intake    participants (minors and young adults), guardians, versioned consent, enrollment, cohorts
--   safety    referrals, mandated reports (ORC 2151.421), incidents
--   collab    data-sharing agreements and grants of access between ICT and KATA
--   research  YVPC measures (survey waves), randomization
--   analytics de-identified views ONLY (analyst role is granted nothing else)
--   grants    GPCS: solicitations, requirements, applications, sections
--   audit     append-only access/change log

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS intake;
CREATE SCHEMA IF NOT EXISTS safety;
CREATE SCHEMA IF NOT EXISTS collab;
CREATE SCHEMA IF NOT EXISTS research;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS grants;
CREATE SCHEMA IF NOT EXISTS audit;

-- ---------------------------------------------------------------- roles
-- Six application roles (from ict.edmhs.us/safeguards). NOLOGIN group roles; real users are members.
DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['edm_admin','edm_clinician','edm_facilitator','edm_program_manager','edm_analyst','edm_intake','edm_grants'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('CREATE ROLE %I NOLOGIN', r);
    END IF;
  END LOOP;
END$$;

-- Salt for pseudonymous research IDs. Rotate per study; never exposed to edm_analyst.
CREATE TABLE core.secret (
  name  text PRIMARY KEY,
  value bytea NOT NULL
);
INSERT INTO core.secret VALUES ('research_id_salt', gen_random_bytes(32)) ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------- core
CREATE TABLE core.organization (
  org_id          serial PRIMARY KEY,
  slug            text UNIQUE NOT NULL,
  legal_name      text NOT NULL,
  applicant_type  text NOT NULL CHECK (applicant_type IN ('nonprofit','for_profit','government','education')),
  uei             text,
  ein             text,
  website         text
);

CREATE TABLE core.program (
  program_id  serial PRIMARY KEY,
  slug        text UNIQUE NOT NULL,            -- ict | kata | pmsg | nabs
  name        text NOT NULL,
  org_id      int NOT NULL REFERENCES core.organization,
  url         text,
  category    text                              -- e.g. training_and_education
);

CREATE TABLE core.staff (
  staff_id            serial PRIMARY KEY,
  db_role             text UNIQUE,             -- the Postgres login role for this person
  full_name           text NOT NULL,
  app_role            text NOT NULL CHECK (app_role IN ('administrator','clinician','facilitator','program_manager','analyst','intake_coordinator')),
  licensure           text,                    -- e.g. 'MD OH 35.xxxxx', 'LISW-S'
  mandated_reporter   boolean NOT NULL DEFAULT true,
  active              boolean NOT NULL DEFAULT true
);

-- ---------------------------------------------------------------- intake
CREATE TABLE intake.cohort (
  cohort_id     serial PRIMARY KEY,
  program_id    int NOT NULL REFERENCES core.program,
  name          text NOT NULL,                  -- e.g. 'Tuesday AM'
  weekday       smallint CHECK (weekday BETWEEN 1 AND 7),
  starts_on     date,
  dev_band      text CHECK (dev_band IN ('10-11','12-14','15-17','18-24','6-9')),
  facilitator   int REFERENCES core.staff
);

CREATE TABLE intake.participant (
  participant_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name      text NOT NULL,
  last_name       text NOT NULL,
  dob             date NOT NULL,
  home_zip        text NOT NULL CHECK (home_zip ~ '^\d{5}$'),
  sex             text,
  medicaid        boolean,
  phone_enc       bytea,                          -- pgp_sym_encrypt; key held by app, not DB
  health_notes_enc bytea,                         -- ORC 3707.511 restricted data
  created_at      timestamptz NOT NULL DEFAULT now(),
  created_by      text NOT NULL DEFAULT current_user
);

CREATE TABLE intake.guardian (
  guardian_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  participant_id  uuid NOT NULL REFERENCES intake.participant ON DELETE CASCADE,
  full_name       text NOT NULL,
  relationship    text NOT NULL,
  phone           text,
  email           text
);

-- Consent language is versioned; a consent row points at the exact text shown.
CREATE TABLE intake.consent_version (
  consent_version_id serial PRIMARY KEY,
  kind        text NOT NULL CHECK (kind IN ('program','research_guardian_permission','research_youth_assent','research_adult_consent','data_linkage','photo_media')),
  version     text NOT NULL,
  body_sha256 text NOT NULL,
  body        text NOT NULL,
  effective   date NOT NULL,
  UNIQUE (kind, version)
);

CREATE TABLE intake.consent (
  consent_id          bigserial PRIMARY KEY,
  participant_id      uuid NOT NULL REFERENCES intake.participant ON DELETE CASCADE,
  consent_version_id  int NOT NULL REFERENCES intake.consent_version,
  signer              text NOT NULL CHECK (signer IN ('guardian','participant')),
  guardian_id         uuid REFERENCES intake.guardian,
  granted             boolean NOT NULL,
  signed_at           timestamptz NOT NULL DEFAULT now(),
  revoked_at          timestamptz,
  captured_by         text NOT NULL DEFAULT current_user,
  CHECK (signer = 'participant' OR guardian_id IS NOT NULL)
);

CREATE TABLE intake.enrollment (
  enrollment_id   bigserial PRIMARY KEY,
  participant_id  uuid NOT NULL REFERENCES intake.participant ON DELETE CASCADE,
  program_id      int NOT NULL REFERENCES core.program,
  cohort_id       int REFERENCES intake.cohort,
  status          text NOT NULL DEFAULT 'requested' CHECK (status IN ('requested','contacted','enrolled','waitlisted','withdrawn','completed')),
  dev_band        text,                           -- facilitator-assessed developmental band (may differ from age)
  requested_at    timestamptz NOT NULL DEFAULT now(),
  enrolled_at     timestamptz,
  UNIQUE (participant_id, program_id)
);

CREATE TABLE intake.attendance (
  enrollment_id  bigint REFERENCES intake.enrollment ON DELETE CASCADE,
  session_date   date NOT NULL,
  present        boolean NOT NULL,
  fidelity_score smallint CHECK (fidelity_score BETWEEN 0 AND 10),
  PRIMARY KEY (enrollment_id, session_date)
);

-- ---------------------------------------------------------------- safety
CREATE TABLE safety.referral (
  referral_id     bigserial PRIMARY KEY,
  participant_id  uuid NOT NULL REFERENCES intake.participant,
  raised_by       int NOT NULL REFERENCES core.staff,
  reason          text NOT NULL,
  referred_to     text NOT NULL,                  -- e.g. 'NHA Behavioral Health'
  consent_basis   text NOT NULL,                  -- ORC 5122.04 basis recorded explicitly
  status          text NOT NULL DEFAULT 'open' CHECK (status IN ('open','accepted','completed','declined')),
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE safety.mandated_report (            -- ORC 2151.421
  report_id       bigserial PRIMARY KEY,
  participant_id  uuid NOT NULL REFERENCES intake.participant,
  raised_by       int NOT NULL REFERENCES core.staff,
  concern         text NOT NULL,
  routed_to       text NOT NULL,                  -- Lucas County Children Services / law enforcement
  reported_at     timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT routed_within_24h CHECK (reported_at IS NULL OR reported_at <= created_at + interval '24 hours')
);

-- ---------------------------------------------------------------- collab (ICT <-> KATA)
CREATE TABLE collab.agreement (
  agreement_id  serial PRIMARY KEY,
  from_program  int NOT NULL REFERENCES core.program,
  to_program    int NOT NULL REFERENCES core.program,
  kind          text NOT NULL CHECK (kind IN ('DUA','BAA','MOU','FERPA')),
  scope         text[] NOT NULL,                  -- e.g. {enrollment,attendance,referral}
  effective     daterange NOT NULL
);

CREATE TABLE collab.access_grant (
  grant_id      bigserial PRIMARY KEY,
  agreement_id  int NOT NULL REFERENCES collab.agreement,
  staff_id      int NOT NULL REFERENCES core.staff,
  participant_id uuid REFERENCES intake.participant,  -- NULL = all participants under the agreement
  granted_at    timestamptz NOT NULL DEFAULT now(),
  expires_at    timestamptz NOT NULL,
  reason        text NOT NULL
);

-- ---------------------------------------------------------------- research
CREATE TABLE research.randomization (
  participant_id uuid PRIMARY KEY REFERENCES intake.participant,
  study          text NOT NULL DEFAULT 'ICT-YVPC-A',
  stratum        text NOT NULL,                  -- dev_band x sex
  arm            text NOT NULL CHECK (arm IN ('ict','waitlist')),
  wave           smallint NOT NULL,
  randomized_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE research.survey (
  participant_id  uuid REFERENCES intake.participant,
  wave_month      smallint NOT NULL CHECK (wave_month IN (0,6,12)),
  fights_30d      smallint,
  bully_perp      numeric(4,2),
  bully_victim    numeric(4,2),
  weapon_30d      boolean,
  ders_sf         numeric(5,2),
  connectedness   numeric(4,2),
  food_insecure   boolean,
  completed_at    timestamptz DEFAULT now(),
  PRIMARY KEY (participant_id, wave_month)
);

-- ---------------------------------------------------------------- grants (GPCS)
CREATE TABLE grants.solicitation (
  solicitation_id   serial PRIMARY KEY,
  opportunity_number text UNIQUE NOT NULL,
  title             text NOT NULL,
  agency            text,
  status            text,
  due_date          date,
  award_ceiling     numeric,
  total_funding     numeric,
  expected_awards   int,
  is_research       boolean,
  parsed            jsonb NOT NULL                  -- full GPCS parse
);

CREATE TABLE grants.application (
  application_id   serial PRIMARY KEY,
  solicitation_id  int NOT NULL REFERENCES grants.solicitation,
  org_id           int NOT NULL REFERENCES core.organization,
  program_id       int REFERENCES core.program,
  package          text NOT NULL,                 -- sf424_rr | sf424
  status           text NOT NULL DEFAULT 'drafting' CHECK (status IN ('drafting','internal_review','submitted','funded','declined')),
  requested_amount numeric
);

CREATE TABLE grants.section (
  application_id int REFERENCES grants.application ON DELETE CASCADE,
  component_id   text NOT NULL,
  title          text NOT NULL,
  body_md        text,
  gaps           text[] DEFAULT '{}',
  updated_at     timestamptz DEFAULT now(),
  PRIMARY KEY (application_id, component_id)
);

-- ---------------------------------------------------------------- audit
CREATE TABLE audit.log (
  id          bigserial PRIMARY KEY,
  at          timestamptz NOT NULL DEFAULT now(),
  actor       text NOT NULL DEFAULT current_user,
  tbl         text NOT NULL,
  op          text NOT NULL,
  row_pk      text,
  diff        jsonb
);

CREATE OR REPLACE FUNCTION audit.capture() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE pk text;
BEGIN
  pk := coalesce(to_jsonb(NEW), to_jsonb(OLD)) ->> TG_ARGV[0];
  INSERT INTO audit.log(tbl, op, row_pk, diff)
  VALUES (TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME, TG_OP, pk,
          CASE WHEN TG_OP = 'UPDATE' THEN jsonb_build_object('old', to_jsonb(OLD) - 'phone_enc' - 'health_notes_enc',
                                                              'new', to_jsonb(NEW) - 'phone_enc' - 'health_notes_enc')
               ELSE NULL END);
  RETURN coalesce(NEW, OLD);
END$$;

CREATE TRIGGER t_audit_participant AFTER INSERT OR UPDATE OR DELETE ON intake.participant
  FOR EACH ROW EXECUTE FUNCTION audit.capture('participant_id');
CREATE TRIGGER t_audit_consent AFTER INSERT OR UPDATE ON intake.consent
  FOR EACH ROW EXECUTE FUNCTION audit.capture('consent_id');
CREATE TRIGGER t_audit_mandated AFTER INSERT OR UPDATE ON safety.mandated_report
  FOR EACH ROW EXECUTE FUNCTION audit.capture('report_id');

-- ---------------------------------------------------------------- de-identified analytics
CREATE OR REPLACE FUNCTION analytics.research_id(p uuid) RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
  SELECT encode(public.hmac(p::text::bytea, (SELECT value FROM core.secret WHERE name = 'research_id_salt'), 'sha256'), 'hex')
$$;

-- Age in whole years at enrollment, ZIP3 only for small cells, no names/DOB/contacts.
CREATE OR REPLACE VIEW analytics.participant_deid WITH (security_barrier) AS
SELECT analytics.research_id(p.participant_id) AS rid,
       extract(year FROM age(coalesce(e.enrolled_at, e.requested_at), p.dob))::int AS age_at_enroll,
       p.home_zip, p.sex, p.medicaid,
       pr.slug AS program, e.status, e.dev_band,
       r.arm, r.wave
FROM intake.participant p
JOIN intake.enrollment e USING (participant_id)
JOIN core.program pr USING (program_id)
LEFT JOIN research.randomization r USING (participant_id);

CREATE OR REPLACE VIEW analytics.survey_deid WITH (security_barrier) AS
SELECT analytics.research_id(s.participant_id) AS rid, s.wave_month, s.fights_30d, s.bully_perp,
       s.bully_victim, s.weapon_30d, s.ders_sf, s.connectedness, s.food_insecure
FROM research.survey s;

CREATE OR REPLACE VIEW analytics.attendance_deid WITH (security_barrier) AS
SELECT analytics.research_id(e.participant_id) AS rid, a.session_date, a.present, a.fidelity_score
FROM intake.attendance a JOIN intake.enrollment e USING (enrollment_id);

-- ---------------------------------------------------------------- privileges + RLS
REVOKE ALL ON ALL TABLES IN SCHEMA core, intake, safety, collab, research, grants, audit FROM PUBLIC;
REVOKE ALL ON core.secret FROM PUBLIC;

GRANT USAGE ON SCHEMA core, intake, safety, collab, research, analytics, grants, audit TO edm_admin;
GRANT ALL ON ALL TABLES IN SCHEMA core, intake, safety, collab, research, grants TO edm_admin;
GRANT SELECT ON ALL TABLES IN SCHEMA audit, analytics TO edm_admin;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA core, intake, safety, collab, research, grants TO edm_admin;
REVOKE ALL ON core.secret FROM edm_admin;

-- intake coordinator: create and edit intake; no clinical/safety detail
GRANT USAGE ON SCHEMA core, intake TO edm_intake;
GRANT SELECT ON core.program, intake.cohort, intake.consent_version TO edm_intake;
GRANT SELECT, INSERT, UPDATE ON intake.participant, intake.guardian, intake.enrollment, intake.consent TO edm_intake;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA intake TO edm_intake;

-- facilitator: own cohort's participants only (RLS below), attendance, raise referral/mandated report
GRANT USAGE ON SCHEMA core, intake, safety TO edm_facilitator;
GRANT SELECT ON core.program, core.staff, intake.cohort, intake.enrollment TO edm_facilitator;
GRANT SELECT (participant_id, first_name, last_name, dob, health_notes_enc) ON intake.participant TO edm_facilitator;
GRANT SELECT, INSERT, UPDATE ON intake.attendance TO edm_facilitator;
GRANT INSERT ON safety.referral, safety.mandated_report TO edm_facilitator;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA safety TO edm_facilitator;

-- clinician (KATA): full participant + safety; collab grants checked by RLS
GRANT USAGE ON SCHEMA core, intake, safety, collab, research TO edm_clinician;
GRANT SELECT ON ALL TABLES IN SCHEMA core, intake, collab TO edm_clinician;
GRANT SELECT, INSERT, UPDATE ON safety.referral, safety.mandated_report TO edm_clinician;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA safety TO edm_clinician;
REVOKE ALL ON core.secret FROM edm_clinician;

-- program manager: operations, no clinical
GRANT USAGE ON SCHEMA core, intake, grants TO edm_program_manager;
GRANT SELECT ON core.program, core.staff, intake.cohort, intake.enrollment, intake.attendance TO edm_program_manager;
GRANT SELECT, INSERT, UPDATE ON intake.cohort TO edm_program_manager;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA intake TO edm_program_manager;

-- analyst: de-identified views ONLY
GRANT USAGE ON SCHEMA analytics TO edm_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO edm_analyst;

-- grants (GPCS)
GRANT USAGE ON SCHEMA grants, core TO edm_grants;
GRANT SELECT ON core.organization, core.program TO edm_grants;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA grants TO edm_grants;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA grants TO edm_grants;

-- Row-level security: a facilitator sees only participants enrolled in a cohort they facilitate;
-- a clinician sees participants with an active collab.access_grant (or all, if grant has NULL participant).
ALTER TABLE intake.participant ENABLE ROW LEVEL SECURITY;
ALTER TABLE intake.enrollment ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION core.current_staff_id() RETURNS int LANGUAGE sql STABLE AS $$
  SELECT staff_id FROM core.staff WHERE db_role = session_user AND active
$$;

CREATE POLICY p_admin_all ON intake.participant TO edm_admin, edm_intake USING (true) WITH CHECK (true);
CREATE POLICY p_fac ON intake.participant FOR SELECT TO edm_facilitator USING (
  EXISTS (SELECT 1 FROM intake.enrollment e JOIN intake.cohort c USING (cohort_id)
          WHERE e.participant_id = participant.participant_id AND c.facilitator = core.current_staff_id()));
CREATE POLICY p_clin ON intake.participant FOR SELECT TO edm_clinician USING (
  EXISTS (SELECT 1 FROM collab.access_grant g
          WHERE g.staff_id = core.current_staff_id() AND g.expires_at > now()
            AND (g.participant_id IS NULL OR g.participant_id = participant.participant_id)));

CREATE POLICY e_admin_all ON intake.enrollment TO edm_admin, edm_intake, edm_program_manager USING (true) WITH CHECK (true);
CREATE POLICY e_fac ON intake.enrollment FOR SELECT TO edm_facilitator USING (
  cohort_id IN (SELECT cohort_id FROM intake.cohort WHERE facilitator = core.current_staff_id()));
CREATE POLICY e_clin ON intake.enrollment FOR SELECT TO edm_clinician USING (
  EXISTS (SELECT 1 FROM collab.access_grant g
          WHERE g.staff_id = core.current_staff_id() AND g.expires_at > now()
            AND (g.participant_id IS NULL OR g.participant_id = enrollment.participant_id)));

-- Analytics views run as their owner (bypass RLS) but expose no identifiers.
GRANT EXECUTE ON FUNCTION analytics.research_id(uuid) TO edm_analyst;
