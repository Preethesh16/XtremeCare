-- XtremeCare Supabase Schema
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor → New Query)

-- 1. Patients table
CREATE TABLE patients (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  caregiver_id UUID REFERENCES auth.users(id) NOT NULL,
  name TEXT NOT NULL,
  age INTEGER,
  face_enrolled BOOLEAN DEFAULT false,
  fcm_token TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Schedules table
CREATE TABLE schedules (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
  session TEXT CHECK (session IN ('MORNING', 'AFTERNOON', 'NIGHT')) NOT NULL,
  tablet_name TEXT NOT NULL,
  dosage TEXT NOT NULL,
  scheduled_time TIME NOT NULL,
  slot_number INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Dose logs table
CREATE TABLE dose_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
  session TEXT CHECK (session IN ('MORNING', 'AFTERNOON', 'NIGHT')) NOT NULL,
  status TEXT CHECK (status IN ('VERIFIED', 'MISSED', 'PENDING')) DEFAULT 'PENDING',
  dispensed_at TIMESTAMPTZ,
  verified_at TIMESTAMPTZ,
  delay_seconds INTEGER,
  date DATE DEFAULT CURRENT_DATE
);

-- 4. Alerts table
CREATE TABLE alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  patient_id UUID REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
  type TEXT CHECK (type IN ('MISSED_DOSE', 'UNVERIFIED_INTAKE')) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE dose_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- RLS Policies: caregivers can only access their own patient's data
CREATE POLICY "Caregivers can view their patients"
  ON patients FOR ALL
  USING (caregiver_id = auth.uid());

CREATE POLICY "Caregivers can manage their patient schedules"
  ON schedules FOR ALL
  USING (patient_id IN (SELECT id FROM patients WHERE caregiver_id = auth.uid()));

CREATE POLICY "Caregivers can view their patient dose logs"
  ON dose_logs FOR ALL
  USING (patient_id IN (SELECT id FROM patients WHERE caregiver_id = auth.uid()));

CREATE POLICY "Caregivers can manage their patient alerts"
  ON alerts FOR ALL
  USING (patient_id IN (SELECT id FROM patients WHERE caregiver_id = auth.uid()));
