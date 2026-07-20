# 💰 Tap Tycoon

A tap-to-earn money game for your phone, inspired by idle business tycoon games.
Tap your character to make money, then spend it on businesses, upgrades, powerups
and style items to become a billionaire.

## 🎮 Features

- **👆 Tap to earn** — tap the character, watch the cash fly (with haptics + sound)
- **🏢 8 businesses** — from Lemonade Stand to Space Company, each earns money per second automatically
- **⬆️ Tap upgrades** — 5 upgrade lines that multiply how much each tap is worth
- **⚡ Powerups** — Coffee Rush (2× tap), Golden Frenzy (3× everything), Money Rain and Time Warp (instant cash). Prices scale with your income so they always stay useful
- **👕 Style shop** — hats, glasses, bling and auras. Your character visibly wears what you buy, and every item gives a permanent income bonus
- **😎 Evolving avatar** — your character's face gets happier (and greedier) as you get richer
- **💤 Offline earnings** — your businesses keep working while the app is closed (up to 2 hours), collected in a "Welcome back" screen
- **💾 Auto-save** — progress saves automatically to your device; works fully offline once installed

## 📱 How to get it on your phone (what YOU need to do)

The game is a **PWA (Progressive Web App)** — no app store needed:

1. **Enable GitHub Pages** (one-time):
   - Merge this branch to `main` (or push it as `main`)
   - In this repo go to **Settings → Pages → Source** and choose **GitHub Actions**
   - The included workflow (`.github/workflows/deploy.yml`) deploys the game automatically on every push
2. **Open the game on your phone** at:
   `https://tomesortiz-debug.github.io/joyam/`
3. **Install it like a real app**:
   - **Android (Chrome):** tap the ⋮ menu → **Add to Home screen** → Install
   - **iPhone (Safari):** tap Share → **Add to Home Screen**

It then launches full-screen with its own icon, works offline, and keeps your save.

You can also test it right now on a computer by just opening `index.html` in a browser.

## 🚀 Optional next steps (to go further)

- **Real Android app (Play Store):** wrap the deployed URL with [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap) (TWA) or [Capacitor](https://capacitorjs.com/) — needs a Google Play developer account ($25 one-time)
- **Cloud save / leaderboards:** would need a small backend (e.g. Firebase)
- **More content:** prestige/rebirth system, achievements, more items — just ask!

## 🛠️ Tech

Pure HTML/CSS/JavaScript — no frameworks, no build step, single `index.html`.
Includes a web app manifest, service worker (offline support) and generated icons.
