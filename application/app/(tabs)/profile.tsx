import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { StatusBadge } from '@/components/StatusBadge';
import { AppColors } from '@/constants/theme';
import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import type { Patient } from '@/types';

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchPatient = useCallback(async () => {
    if (!user) return;

    const { data } = await supabase
      .from('patients')
      .select('*')
      .eq('caregiver_id', user.id)
      .single();

    setPatient(data);
    setLoading(false);
  }, [user]);

  useEffect(() => {
    fetchPatient();
  }, [fetchPatient]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={AppColors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Profile</Text>

      <View style={styles.card}>
        <View style={styles.avatar}>
          <MaterialIcons name="person" size={40} color={AppColors.primary} />
        </View>

        {patient ? (
          <>
            <InfoRow label="Patient Name" value={patient.name} />
            <InfoRow label="Age" value={patient.age != null ? String(patient.age) : 'N/A'} />
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Face Enrollment</Text>
              <StatusBadge
                label={patient.face_enrolled ? 'Enrolled' : 'Not Enrolled'}
                color={patient.face_enrolled ? AppColors.verified : AppColors.warning}
              />
            </View>
          </>
        ) : (
          <Text style={styles.noPatient}>No patient linked to this account</Text>
        )}
      </View>

      <View style={styles.card}>
        <InfoRow label="Caregiver Email" value={user?.email ?? 'N/A'} />
      </View>

      <Pressable style={styles.logoutButton} onPress={signOut}>
        <MaterialIcons name="logout" size={20} color={AppColors.danger} />
        <Text style={styles.logoutText}>Sign Out</Text>
      </Pressable>
    </ScrollView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
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
    marginBottom: 20,
  },
  card: {
    backgroundColor: AppColors.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 1,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: AppColors.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  infoLabel: {
    fontSize: 14,
    color: AppColors.textSecondary,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: AppColors.textPrimary,
  },
  noPatient: {
    fontSize: 14,
    color: AppColors.textSecondary,
    textAlign: 'center',
    paddingVertical: 16,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: AppColors.card,
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
    borderWidth: 1,
    borderColor: AppColors.danger + '30',
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: AppColors.danger,
  },
});
