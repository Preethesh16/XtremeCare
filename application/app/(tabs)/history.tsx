import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  SectionList,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { StatusBadge } from '@/components/StatusBadge';
import { AppColors } from '@/constants/theme';
import { useAuth } from '@/lib/auth-context';
import { supabase } from '@/lib/supabase';
import type { DoseLog, DoseStatus } from '@/types';

const STATUS_COLORS: Record<DoseStatus, string> = {
  VERIFIED: AppColors.verified,
  MISSED: AppColors.missed,
  PENDING: AppColors.pending,
};

interface Section {
  title: string;
  data: DoseLog[];
}

export default function HistoryScreen() {
  const { user } = useAuth();
  const [sections, setSections] = useState<Section[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = useCallback(async () => {
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

    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    const fromDate = sevenDaysAgo.toISOString().split('T')[0];

    const { data: logs } = await supabase
      .from('dose_logs')
      .select('*, schedules(*)')
      .eq('patient_id', patient.id)
      .gte('date', fromDate)
      .order('date', { ascending: false });

    const grouped = new Map<string, DoseLog[]>();
    (logs ?? []).forEach((log: DoseLog) => {
      const existing = grouped.get(log.date) ?? [];
      existing.push(log);
      grouped.set(log.date, existing);
    });

    const result: Section[] = Array.from(grouped.entries()).map(([date, data]) => ({
      title: formatDate(date),
      data,
    }));

    setSections(result);
    setLoading(false);
  }, [user]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={AppColors.primary} />
      </View>
    );
  }

  if (sections.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>No dose history yet</Text>
        <Text style={styles.emptySubtext}>Dose logs will appear here once recorded</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SectionList
        sections={sections}
        contentContainerStyle={styles.content}
        keyExtractor={(item) => item.id}
        renderSectionHeader={({ section }) => (
          <Text style={styles.sectionHeader}>{section.title}</Text>
        )}
        ListHeaderComponent={<Text style={styles.title}>History</Text>}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View style={styles.rowLeft}>
              <StatusBadge label={item.session} color={AppColors.primary} />
              <Text style={styles.tablet}>
                {item.schedules?.tablet_name ?? 'Unknown'}
              </Text>
            </View>
            <View style={styles.rowRight}>
              <StatusBadge label={item.status} color={STATUS_COLORS[item.status]} />
              {item.delay_seconds != null && item.delay_seconds > 0 && (
                <Text style={styles.delay}>+{Math.round(item.delay_seconds / 60)}min</Text>
              )}
            </View>
          </View>
        )}
      />
    </View>
  );
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diff = today.getTime() - date.getTime();
  const days = Math.round(diff / 86400000);

  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  return date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
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
  sectionHeader: {
    fontSize: 16,
    fontWeight: '700',
    color: AppColors.textPrimary,
    marginTop: 16,
    marginBottom: 8,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: AppColors.card,
    borderRadius: 10,
    padding: 14,
    marginBottom: 6,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  rowRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  tablet: {
    fontSize: 14,
    color: AppColors.textPrimary,
  },
  delay: {
    fontSize: 12,
    color: AppColors.warning,
    fontWeight: '600',
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
