-- Reference data only (organizations, programs, demo staff, cohorts, consent text). Safe for production after editing staff.
INSERT INTO core.organization (slug, legal_name, applicant_type, uei, website) VALUES
  ('edmhs_org', 'Empowered Disease Management Health Services (EDMHS.org)', 'nonprofit', NULL, 'https://edmhs.org'),
  ('edm_health_services_llc', 'EDM Health Services, LLC', 'for_profit', 'FSMJREGJGPJ3', 'https://www.edmhs.us');

INSERT INTO core.program (slug, name, org_id, url, category) VALUES
  ('ict',  'Inner Combat Training',                (SELECT org_id FROM core.organization WHERE slug='edmhs_org'), 'https://ict.edmhs.us',  'youth_violence_prevention'),
  ('kata', 'KATA records and safety platform',     (SELECT org_id FROM core.organization WHERE slug='edm_health_services_llc'), 'https://kata.edmhs.us', 'platform'),
  ('pmsg', 'Pain Management Support Group',        (SELECT org_id FROM core.organization WHERE slug='edmhs_org'), 'https://pmsg.edmhs.us', 'training_and_education');

INSERT INTO core.staff (db_role, full_name, app_role, licensure) VALUES
  ('dr_hall',   'Darrell A. Hall, MD', 'administrator', 'MD (Ohio)'),
  ('fac_demo',  'Demo Facilitator',    'facilitator',   NULL),
  ('clin_demo', 'Demo Clinician',      'clinician',     'LISW-S (demo)'),
  ('ana_demo',  'Demo Analyst',        'analyst',       NULL);

INSERT INTO intake.cohort (program_id, name, weekday, dev_band, facilitator)
SELECT p.program_id, x.name, x.wd, x.band, (SELECT staff_id FROM core.staff WHERE db_role='fac_demo')
FROM core.program p, (VALUES ('Monday 10-11', 1, '10-11'), ('Tuesday 12-14', 2, '12-14'),
                             ('Wednesday 15-17', 3, '15-17'), ('Thursday peer mentors', 4, '18-24')) AS x(name, wd, band)
WHERE p.slug = 'ict';

INSERT INTO intake.consent_version (kind, version, body_sha256, body, effective) VALUES
  ('program', '2026.1', encode(digest('ICT program participation consent v2026.1 (placeholder text)', 'sha256'), 'hex'),
   'ICT program participation consent v2026.1 (placeholder text)', '2026-12-01');

