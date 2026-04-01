import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { VoiceInput } from '@/components/VoiceInput';
import { AppColors } from '@/constants/theme';
import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import type { SessionType } from '@/types';

const SESSIONS: SessionType[] = ['MORNING', 'AFTERNOON', 'NIGHT'];

interface ScheduleForm {
  tablet_name: string;
  dosage: string;
  morning_time: string;
  afternoon_time: string;
  night_time: string;
  slot_number: string;
}

const EMPTY_FORM: ScheduleForm = {
  tablet_name: '',
  dosage: '',
  morning_time: '08:00',
  afternoon_time: '14:00',
  night_time: '21:00',
  slot_number: '1',
};

export default function ScheduleScreen() {
  const { user } = useAuth();
  const [form, setForm] = useState<ScheduleForm>(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [patientId, setPatientId] = useState<string | null>(null);

  const loadSchedule = useCallback(async () => {
    if (!user) return;

    const { data: patient } = await supabase
      .from('patients')
      .select('id')
      .eq('caregiver_id', user.id)
      .single();

    if (!patient) {
      setLoading(false);
      return;
    }

    setPatientId(patient.id);

    const { data: schedules } = await supabase
      .from('schedules')
      .select('*')
      .eq('patient_id', patient.id);

    if (schedules && schedules.length > 0) {
      const first = schedules[0];
      const timeMap: Record<string, string> = {};
      schedules.forEach((s) => {
        timeMap[s.session] = s.scheduled_time;
      });

      setForm({
        tablet_name: first.tablet_name,
        dosage: first.dosage,
        morning_time: timeMap.MORNING ?? '08:00',
        afternoon_time: timeMap.AFTERNOON ?? '14:00',
        night_time: timeMap.NIGHT ?? '21:00',
        slot_number: String(first.slot_number ?? 1),
      });
    }

    setLoading(false);
  }, [user]);

  useEffect(() => {
    loadSchedule();
  }, [loadSchedule]);

  const handleSave = async () => {
    if (!patientId) {
      Alert.alert('Error', 'No patient found. Please set up a patient first.');
      return;
    }

    if (!form.tablet_name.trim() || !form.dosage.trim()) {
      Alert.alert('Error', 'Please fill in tablet name and dosage.');
      return;
    }

    setSaving(true);

    const timeMap: Record<SessionType, string> = {
      MORNING: form.morning_time,
      AFTERNOON: form.afternoon_time,
      NIGHT: form.night_time,
    };

    // Delete existing schedules for this patient then insert new ones
    await supabase.from('schedules').delete().eq('patient_id', patientId);

    const rows = SESSIONS.map((session) => ({
      patient_id: patientId,
      session,
      tablet_name: form.tablet_name.trim(),
      dosage: form.dosage.trim(),
      scheduled_time: timeMap[session],
      slot_number: parseInt(form.slot_number, 10) || 1,
    }));

    const { error } = await supabase.from('schedules').insert(rows);

    setSaving(false);

    if (error) {
      Alert.alert('Error', error.message);
    } else {
      Alert.alert('Success', 'Schedule saved successfully.');
    }
  };

  const updateField = (key: keyof ScheduleForm, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={AppColors.primary} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Schedule</Text>

        <Text style={styles.label}>Tablet Name</Text>
        <View style={styles.voiceRow}>
          <TextInput
            style={[styles.input, styles.voiceInput]}
            value={form.tablet_name}
            onChangeText={(v) => updateField('tablet_name', v)}
            placeholder="e.g. Metformin"
            placeholderTextColor={AppColors.textSecondary}
          />
          <VoiceInput onResult={(text) => updateField('tablet_name', text)} />
        </View>

        <Text style={styles.label}>Dosage</Text>
        <View style={styles.voiceRow}>
          <TextInput
            style={[styles.input, styles.voiceInput]}
            value={form.dosage}
            onChangeText={(v) => updateField('dosage', v)}
            placeholder="e.g. 500mg"
            placeholderTextColor={AppColors.textSecondary}
          />
          <VoiceInput onResult={(text) => updateField('dosage', text)} />
        </View>

        <Text style={styles.label}>Morning Time</Text>
        <TextInput
          style={styles.input}
          value={form.morning_time}
          onChangeText={(v) => updateField('morning_time', v)}
          placeholder="HH:MM"
          placeholderTextColor={AppColors.textSecondary}
        />

        <Text style={styles.label}>Afternoon Time</Text>
        <TextInput
          style={styles.input}
          value={form.afternoon_time}
          onChangeText={(v) => updateField('afternoon_time', v)}
          placeholder="HH:MM"
          placeholderTextColor={AppColors.textSecondary}
        />

        <Text style={styles.label}>Night Time</Text>
        <TextInput
          style={styles.input}
          value={form.night_time}
          onChangeText={(v) => updateField('night_time', v)}
          placeholder="HH:MM"
          placeholderTextColor={AppColors.textSecondary}
        />

        <Text style={styles.label}>Slot Number</Text>
        <TextInput
          style={styles.input}
          value={form.slot_number}
          onChangeText={(v) => updateField('slot_number', v)}
          placeholder="1"
          placeholderTextColor={AppColors.textSecondary}
          keyboardType="numeric"
        />

        <Pressable
          style={[styles.button, saving && styles.buttonDisabled]}
          onPress={handleSave}
          disabled={saving}>
          {saving ? (
            <ActivityIndicator color={AppColors.card} />
          ) : (
            <Text style={styles.buttonText}>Save Schedule</Text>
          )}
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: AppColors.background,
  },
  content: {
    padding: 20,
    paddingTop: 60,
    paddingBottom: 40,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: AppColors.background,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: AppColors.textPrimary,
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: AppColors.textPrimary,
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    backgroundColor: AppColors.card,
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    color: AppColors.textPrimary,
  },
  voiceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  voiceInput: {
    flex: 1,
  },
  button: {
    backgroundColor: AppColors.primary,
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: AppColors.card,
    fontSize: 16,
    fontWeight: '700',
  },
});
