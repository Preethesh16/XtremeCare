import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { SessionCard } from '@/components/SessionCard';
import { AppColors } from '@/constants/theme';
import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import type { DoseLog, DoseStatus, SessionType } from '@/types';

const SESSIONS: SessionType[] = ['MORNING', 'AFTERNOON', 'NIGHT'];

interface SessionData {
  session: SessionType;
  tabletName: string;
  scheduledTime: string;
  status: DoseStatus;
}

export default function DashboardScreen() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<SessionData[]>([]);
  const [lastSync, setLastSync] = useState<Date>(new Date());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboard = useCallback(async () => {
    if (!user) return;

    const { data: patient } = await supabase
      .from('patients')
      .select('id')
      .eq('caregiver_id', user.id)
      .single();

    if (!patient) {
      setSessions(SESSIONS.map((s) => ({ session: s, tabletName: '', scheduledTime: '--:--', status: 'PENDING' })));
      setLoading(false);
      return;
    }

    const today = new Date().toISOString().split('T')[0];

    const { data: logs } = await supabase
      .from('dose_logs')
      .select('*, schedules(*)')
      .eq('patient_id', patient.id)
      .eq('date', today);

    const sessionMap = new Map<SessionType, DoseLog>();
    (logs ?? []).forEach((log: DoseLog) => sessionMap.set(log.session, log));

    const result: SessionData[] = SESSIONS.map((s) => {
      const log = sessionMap.get(s);
      return {
        session: s,
        tabletName: log?.schedules?.tablet_name ?? '',
        scheduledTime: log?.schedules?.scheduled_time ?? '--:--',
        status: log?.status ?? 'PENDING',
      };
    });

    setSessions(result);
    setLastSync(new Date());
    setLoading(false);
  }, [user]);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchDashboard();
    setRefreshing(false);
  };

  const verified = sessions.filter((s) => s.status === 'VERIFIED').length;
  const adherence = sessions.length > 0 ? Math.round((verified / sessions.length) * 100) : 0;

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={AppColors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={AppColors.primary} />}>
      <Text style={styles.title}>Dashboard</Text>

      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{adherence}%</Text>
          <Text style={styles.statLabel}>Today&apos;s Adherence</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{lastSync.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</Text>
          <Text style={styles.statLabel}>Last Sync</Text>
        </View>
      </View>

      {sessions.map((s) => (
        <SessionCard
          key={s.session}
          session={s.session}
          tabletName={s.tabletName}
          scheduledTime={s.scheduledTime}
          status={s.status}
        />
      ))}
    </ScrollView>
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
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: AppColors.card,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 1,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '700',
    color: AppColors.primary,
  },
  statLabel: {
    fontSize: 12,
    color: AppColors.textSecondary,
    marginTop: 4,
  },
});
