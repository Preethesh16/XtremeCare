-- backend/db/policies.sql

alter table patients enable row level security;
alter table schedules enable row level security;
alter table dose_logs enable row level security;
alter table alerts enable row level security;

create policy "caregiver owns patient"
on patients for all
using (auth.uid() = caregiver_id);

create policy "caregiver owns schedules"
on schedules for all
using (
  patient_id in (
    select id from patients where caregiver_id = auth.uid()
  )
);

create policy "caregiver owns logs"
on dose_logs for all
using (
  patient_id in (
    select id from patients where caregiver_id = auth.uid()
  )
);

create policy "caregiver owns alerts"
on alerts for all
using (
  patient_id in (
    select id from patients where caregiver_id = auth.uid()
  )
);
