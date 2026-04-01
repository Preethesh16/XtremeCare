export type SessionType = 'MORNING' | 'AFTERNOON' | 'NIGHT';

export type DoseStatus = 'VERIFIED' | 'MISSED' | 'PENDING';

export type AlertType = 'MISSED_DOSE' | 'UNVERIFIED_INTAKE';

export interface Patient {
  id: string;
  caregiver_id: string;
  name: string;
  age: number | null;
  face_enrolled: boolean;
  fcm_token: string | null;
  created_at: string;
}

export interface Schedule {
  id: string;
  patient_id: string;
  session: SessionType;
  tablet_name: string;
  dosage: string;
  scheduled_time: string;
  slot_number: number | null;
  created_at: string;
}

export interface DoseLog {
  id: string;
  patient_id: string;
  session: SessionType;
  status: DoseStatus;
  dispensed_at: string | null;
  verified_at: string | null;
  delay_seconds: number | null;
  date: string;
  // joined from schedules
  schedules?: Schedule;
}

export interface Alert {
  id: string;
  patient_id: string;
  type: AlertType;
  message: string;
  is_read: boolean;
  created_at: string;
}
