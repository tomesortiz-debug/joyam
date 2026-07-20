# Tap Tycoon

A tap-to-earn idle tycoon game for phones, with full vector art and a real
Android app build for the Google Play Store.

Play in browser / install as web app: **https://tomesortiz-debug.github.io/joyam/**

## Features

- **Tap to earn** — tap your tycoon character, cash flies out (haptics + sound)
- **Vector art** — hand-drawn SVG character whose hats, glasses and bling visibly
  change when equipped; custom icons for every item; city skyline backdrop
- **8 businesses** with passive income and **milestones**: every 10 owned doubles
  that business's income (progress bars in each row)
- **Buy ×1 / ×10 / MAX** bulk purchasing
- **5 tap upgrades**, **4 powerups** with income-scaled prices, **Daily Gift**
- **Style shop** — 12 items across hats / glasses / bling / auras, each with a
  permanent income bonus
- **14 achievements** with progress bars and permanent rewards
- **Prestige** — reset your run for +10% ALL income per point, forever
- **Offline earnings** (2h cap), auto-save, works fully offline

## Project layout

| Path | What it is |
|---|---|
| `www/` | The game itself (single-file HTML5, no dependencies) |
| `android/` | Native Android app (Capacitor wrapper around `www/`) |
| `capacitor.config.json` | App id/name for the Android build |
| `.github/workflows/deploy.yml` | Publishes `www/` to GitHub Pages on every push to main |
| `.github/workflows/build-android.yml` | Builds the Play Store AAB + installable APKs on every push to main |

## Install on Android — free, no Play Store needed

**Direct download:** https://github.com/tomesortiz-debug/joyam/releases/latest/download/TapTycoon.apk

Open that link on your Android phone, allow the install when prompted, and the
game appears on your home screen as a real app. Every push to `main` rebuilds
it automatically and updates the link.

## Getting the Play Store build (when you're ready)

Every push to `main` runs the **Build Android app** workflow. Open the run in
the Actions tab and download:

- `tap-tycoon-debug-apk` — the same APK as the release link above
- `tap-tycoon-playstore-aab` — upload this file to Google Play Console

### One-time signing setup (needed for the Play Store AAB)

The release build is signed with an upload keystore kept in GitHub secrets
(never committed). In the repo: **Settings → Secrets and variables → Actions**:

1. Under **Secrets**, add `KEYSTORE_BASE64` (the base64 text of the keystore)
   and `KEYSTORE_PASSWORD` (its password)
2. Under **Variables**, add `SIGNING_ENABLED` = `true`

The key alias is `upload`. Keep the keystore file and password backed up —
Play uses them to verify every future update of the app.

### Publishing to Google Play (checklist)

1. Create a Google Play developer account ($25 one-time): https://play.google.com/console
2. Create app → name **Tap Tycoon** (or your own — also change `appName` in
   `capacitor.config.json` and `android/app/src/main/res/values/strings.xml`)
3. Complete the required declarations (content rating, target audience, data
   safety — the game collects **no** data, everything is stored on-device)
4. Upload the `tap-tycoon-playstore-aab` file under **Production → Create release**
   (accept Google-managed app signing when asked)
5. Add store listing assets: description, screenshots (take them from the web
   version on your phone), and the app icon (`www/icon-512.png`)
6. Submit for review

Each new release needs a bumped `versionCode`/`versionName` in
`android/app/build.gradle`.

## Local development

The game is plain HTML/JS — open `www/index.html` in a browser, edit, refresh.
For the Android shell: `npm install`, `npx cap sync android`, then open
`android/` in Android Studio.
