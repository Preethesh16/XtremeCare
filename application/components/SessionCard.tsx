import { StyleSheet, Text, View } from 'react-native';

import { AppColors } from '@/constants/theme';
import type { DoseStatus } from '@/types';

import { StatusBadge } from './StatusBadge';

interface SessionCardProps {
  session: string;
  tabletName: string;
  scheduledTime: string;
  status: DoseStatus;
}

const STATUS_CONFIG: Record<DoseStatus, { label: string; color: string }> = {
  VERIFIED: { label: 'Verified', color: AppColors.verified },
  MISSED: { label: 'Missed', color: AppColors.missed },
  PENDING: { label: 'Pending', color: AppColors.pending },
};

export function SessionCard({ session, tabletName, scheduledTime, status }: SessionCardProps) {
  const { label, color } = STATUS_CONFIG[status];

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.session}>{session}</Text>
        <StatusBadge label={label} color={color} />
      </View>
      <Text style={styles.tablet}>{tabletName || 'No medication scheduled'}</Text>
      <Text style={styles.time}>{scheduledTime}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: AppColors.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  session: {
    fontSize: 16,
    fontWeight: '700',
    color: AppColors.textPrimary,
  },
  tablet: {
    fontSize: 14,
    color: AppColors.textSecondary,
    marginBottom: 4,
  },
  time: {
    fontSize: 13,
    color: AppColors.textSecondary,
  },
});
