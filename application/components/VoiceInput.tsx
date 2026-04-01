import { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useAudioRecorder, RecordingPresets, AudioModule } from 'expo-audio';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { AppColors } from '@/constants/theme';

interface VoiceInputProps {
  onResult: (text: string) => void;
}

export function VoiceInput({ onResult }: VoiceInputProps) {
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [isRecording, setIsRecording] = useState(false);
  const hasPermission = useRef(false);

  const startRecording = async () => {
    try {
      if (!hasPermission.current) {
        const status = await AudioModule.requestRecordingPermissionsAsync();
        if (!status.granted) return;
        hasPermission.current = true;
      }

      recorder.record();
      setIsRecording(true);
    } catch (err) {
      console.error('Failed to start recording:', err);
    }
  };

  const stopRecording = async () => {
    try {
      await recorder.stop();
      setIsRecording(false);

      if (recorder.uri) {
        // The recording URI is available for speech-to-text processing.
        // In production, send this to a speech recognition service (e.g., Google STT, Whisper).
        onResult(`[Voice recorded: ${recorder.uri.split('/').pop()}]`);
      }
    } catch (err) {
      console.error('Failed to stop recording:', err);
    }
  };

  const handlePress = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <View style={styles.container}>
      <Pressable
        style={[styles.button, isRecording && styles.buttonActive]}
        onPress={handlePress}>
        <MaterialIcons
          name="mic"
          size={22}
          color={isRecording ? AppColors.card : AppColors.primary}
        />
      </Pressable>
      {isRecording && (
        <Text style={styles.indicator}>Recording...</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  button: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: AppColors.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: AppColors.primary,
  },
  buttonActive: {
    backgroundColor: AppColors.danger,
    borderColor: AppColors.danger,
  },
  indicator: {
    fontSize: 13,
    color: AppColors.danger,
    fontWeight: '600',
  },
});
