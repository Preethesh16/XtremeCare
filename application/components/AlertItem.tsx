import { Pressable, StyleSheet, Text, View } from 'react-native';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { AppColors } from '@/constants/theme';
import type { Alert } from '@/types';

interface AlertItemProps {
  alert: Alert;
  onPress: () => void;
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

const ICON_MAP: Record<string, { name: 'error' | 'warning'; color: string }> = {
  MISSED_DOSE: { name: 'error', color: AppColors.danger },
  UNVERIFIED_INTAKE: { name: 'warning', color: AppColors.warning },
};

export function AlertItem({ alert, onPress }: AlertItemProps) {
  const icon = ICON_MAP[alert.type] ?? ICON_MAP.MISSED_DOSE;

  return (
    <Pressable style={styles.container} onPress={onPress}>
      <MaterialIcons name={icon.name} size={24} color={icon.color} />
      <View style={styles.content}>
        <Text style={styles.message} numberOfLines={2}>
          {alert.message}
        </Text>
        <Text style={styles.time}>{timeAgo(alert.created_at)}</Text>
      </View>
      {!alert.is_read && <View style={styles.unreadDot} />}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: AppColors.card,
    borderRadius: 12,
    padding: 14,
    marginBottom: 8,
    gap: 12,
  },
  content: {
    flex: 1,
  },
  message: {
    fontSize: 14,
    color: AppColors.textPrimary,
    marginBottom: 4,
  },
  time: {
    fontSize: 12,
    color: AppColors.textSecondary,
  },
  unreadDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: AppColors.primary,
  },
});
