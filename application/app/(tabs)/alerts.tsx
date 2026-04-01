import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { AlertItem } from '@/components/AlertItem';
import { AppColors } from '@/constants/theme';
import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import type { Alert } from '@/types';

export default function AlertsScreen() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
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

    const { data } = await supabase
      .from('alerts')
      .select('*')
      .eq('patient_id', patient.id)
      .order('created_at', { ascending: false });

    setAlerts(data ?? []);
    setLoading(false);
  }, [user]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const markAsRead = async (alertId: string) => {
    await supabase
      .from('alerts')
      .update({ is_read: true })
      .eq('id', alertId);

    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a)),
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={AppColors.primary} />
      </View>
    );
  }

  if (alerts.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>No alerts</Text>
        <Text style={styles.emptySubtext}>You&apos;re all caught up</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={alerts}
        contentContainerStyle={styles.content}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={<Text style={styles.title}>Alerts</Text>}
        renderItem={({ item }) => (
          <AlertItem alert={item} onPress={() => markAsRead(item.id)} />
        )}
      />
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
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: AppColors.textPrimary,
  },
  emptySubtext: {
    fontSize: 14,
    color: AppColors.textSecondary,
    marginTop: 8,
  },
});
