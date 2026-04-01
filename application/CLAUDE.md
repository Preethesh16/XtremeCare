# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm start          # Start Expo dev server
npm run android    # Run on Android emulator/device
npm run ios        # Run on iOS simulator
npm run web        # Run in browser
npm run lint       # Run ESLint (expo lint)
```

## Architecture

This is an **Expo (React Native)** app using **file-based routing** via `expo-router` (similar to Next.js).

### Routing

`app/` is the routing root — every file becomes a route:
- `_layout.tsx` files define navigator wrappers for their directory segment
- `(tabs)/` is a route group (parentheses = no URL segment) containing the bottom tab navigator
- Platform-specific files use `.ios.tsx` / `.web.ts` suffixes (e.g., `components/ui/icon-symbol.ios.tsx`)

### Theme System

Light/dark mode is handled through a layered system:
1. `constants/theme.ts` — static color tokens for both modes
2. `hooks/use-theme-color.ts` — resolves a token to the current mode's color
3. `components/themed-text.tsx`, `components/themed-view.tsx` — drop-in theme-aware primitives

### Path Aliases

`@/` maps to the repo root (configured in `tsconfig.json`). Use `@/components/...`, `@/hooks/...`, etc. for all internal imports.

### Key Config

- `app.json` — Expo config; `typedRoutes` and `reactCompiler` experiments are both enabled
- TypeScript strict mode is on
- ESLint uses flat config (`eslint.config.js`) with `eslint-config-expo/flat`
