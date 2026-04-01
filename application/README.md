# XtremeCare - Caregiver App

A React Native Expo app for caregivers to manage medication dispensing for patients. Built with TypeScript, Expo Router, Supabase, and Firebase Cloud Messaging.

## Features

- **Dashboard** — View today's 3 dose sessions (Morning, Afternoon, Night) with live status and adherence percentage
- **Schedule** — Create and edit medication schedules with voice input for tablet names
- **History** — View dose logs for the last 7 days grouped by date
- **Alerts** — Receive and manage missed dose / unverified intake alerts
- **Profile** — View patient info, face enrollment status, and sign out

## Prerequisites

- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- Expo Go app on your phone (for testing)
- A Supabase project

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the contents of `supabase/schema.sql` to create tables and RLS policies
3. Go to **Authentication > Settings** and enable Email/Password sign-in
4. Create a test user in **Authentication > Users**
5. Insert a patient record linked to your user's ID in the `patients` table

### 3. Configure environment variables

Create a `.env` file in the project root:

```
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

You can find these values in your Supabase project: **Settings > API**.

### 4. Run the app

```bash
# Start Expo dev server
npm start

# Or run on specific platform
npm run android
npm run ios
npm run web
```

Scan the QR code with Expo Go to open on your device.

## Project Structure

```
app/
  _layout.tsx              # Root layout with auth guard
  (auth)/
    _layout.tsx            # Auth stack layout
    login.tsx              # Login screen
  (tabs)/
    _layout.tsx            # Bottom tab navigator (5 tabs)
    index.tsx              # Dashboard screen
    schedule.tsx           # Schedule management + voice input
    history.tsx            # Dose history (last 7 days)
    alerts.tsx             # Alert notifications
    profile.tsx            # Patient profile + logout
lib/
  supabase.ts              # Supabase client initialization
  auth-context.tsx         # Auth context provider + useAuth hook
  notifications.ts         # Push notification helpers
components/
  SessionCard.tsx          # Dose session card (used on dashboard)
  AlertItem.tsx            # Alert row item
  StatusBadge.tsx          # Colored status pill
  VoiceInput.tsx           # Microphone button for voice input
types/
  index.ts                 # TypeScript interfaces and types
supabase/
  schema.sql               # Database schema (run in Supabase SQL Editor)
```

## Environment Variables

| Variable | Description |
|---|---|
| `EXPO_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anonymous/public key |

## Tech Stack

- **Framework:** React Native + Expo SDK 54
- **Routing:** Expo Router v6 (file-based)
- **Backend:** Supabase (Auth + PostgreSQL)
- **Notifications:** Expo Notifications + FCM
- **Audio:** expo-av (for voice input recording)
- **Language:** TypeScript (strict mode)
