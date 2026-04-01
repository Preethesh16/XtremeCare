import { Platform } from 'react-native';
import { router } from 'expo-router';
import Constants from 'expo-constants';

import { supabase } from './supabase';

const isExpoGo = Constants.appOwnership === 'expo';

let Notifications: typeof import('expo-notifications') | null = null;

if (!isExpoGo) {
  try {
    Notifications = require('expo-notifications');
    Notifications!.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
        shouldShowBanner: true,
        shouldShowList: true,
      }),
    });
  } catch {
    console.warn('expo-notifications not available in this environment.');
  }
}

export async function registerForPushNotifications(): Promise<string | null> {
  if (!Notifications) return null;

  const { status: existing } = await Notifications.getPermissionsAsync();
  let finalStatus = existing;

  if (existing !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    return null;
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.HIGH,
    });
  }

  const { data: token } = await Notifications.getExpoPushTokenAsync();
  return token;
}

export async function savePushToken(patientId: string, token: string) {
  await supabase
    .from('patients')
    .update({ fcm_token: token })
    .eq('id', patientId);
}

export function setupNotificationListeners() {
  if (!Notifications) return () => {};

  const responseSubscription = Notifications.addNotificationResponseReceivedListener(() => {
    router.navigate('/(tabs)/alerts' as never);
  });

  return () => {
    responseSubscription.remove();
  };
}
