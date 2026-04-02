-- backend/db/schema.sql
create extension if not exists "pgcrypto";

-- patients table
create table patients (
  id uuid primary key default gen_random_uuid(),
  caregiver_id uuid references auth.users(id) on delete cascade,
  name text not null,
  age integer,
  face_enrolled boolean default false,
  fcm_token text,
  created_at timestamptz default now()
);

-- schedules table
create table schedules (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  session text check (session in ('MORNING','AFTERNOON','NIGHT')),
  tablet_name text not null,
  dosage text not null,
  scheduled_time time not null,
  slot_number integer,
  created_at timestamptz default now()
);

-- logs
create table dose_logs (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  session text check (session in ('MORNING','AFTERNOON','NIGHT')),
  status text check (status in ('VERIFIED','MISSED','PENDING')),
  dispensed_at timestamptz,
  verified_at timestamptz,
  delay_seconds integer,
  date date default current_date
);

-- alerts
create table alerts (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  type text check (type in ('MISSED_DOSE','UNVERIFIED_INTAKE')),
  message text not null,
  is_read boolean default false,
  created_at timestamptz default now()
);
