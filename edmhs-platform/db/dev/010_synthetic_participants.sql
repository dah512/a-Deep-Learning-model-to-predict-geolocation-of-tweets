-- DEV/TEST ONLY: 24 synthetic participants + randomization. Never load into production.
-- 24 synthetic participants spread across bands/ZIPs
WITH s AS (
  SELECT g, (ARRAY['43607','43610','43620'])[1 + g % 3] AS zip,
         (date '2026-12-01' - ((10 + (g % 15)) * 365 + g) )::date AS dob,
         (ARRAY['F','M'])[1 + g % 2] AS sex
  FROM generate_series(1, 24) g
), ins AS (
  INSERT INTO intake.participant (first_name, last_name, dob, home_zip, sex, medicaid)
  SELECT 'Synthetic' || g, 'Youth', dob, zip, sex, (g % 5 <> 0) FROM s
  RETURNING participant_id, dob, sex
)
INSERT INTO intake.enrollment (participant_id, program_id, cohort_id, status, dev_band, enrolled_at)
SELECT i.participant_id, c.program_id, c.cohort_id, 'enrolled', c.dev_band, now()
FROM ins i
JOIN intake.cohort c ON c.dev_band = CASE
   WHEN extract(year FROM age(date '2026-12-01', i.dob)) <= 11 THEN '10-11'
   WHEN extract(year FROM age(date '2026-12-01', i.dob)) <= 14 THEN '12-14'
   WHEN extract(year FROM age(date '2026-12-01', i.dob)) <= 17 THEN '15-17'
   ELSE '18-24' END;

INSERT INTO research.randomization (participant_id, stratum, arm, wave)
SELECT e.participant_id, e.dev_band || ':' || p.sex,
       CASE WHEN row_number() OVER (PARTITION BY e.dev_band, p.sex ORDER BY e.participant_id) % 2 = 0 THEN 'ict' ELSE 'waitlist' END, 1
FROM intake.enrollment e JOIN intake.participant p USING (participant_id);
