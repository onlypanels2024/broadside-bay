# Broadside Bay

Online pirate-ship battles on a Caribbean sea, for Android. Inspired by the 90s PlayStation game Overboard!.

## What's in here

| Folder / file | What it is |
|---|---|
| `www/` | The game itself (3D, Three.js), plus the Firebase online-play connection in `www/js/net-firebase.js` |
| `src-artifact.html` + `build_app.py` | The game's source and the script that turns it into `www/index.html` |
| `android-app/` | The Android app wrapper (Capacitor), app icon and splash screen |
| `functions/` | The **referee**: checks every hit and sinking between players on Firebase's servers |
| `database.rules.json` | Database security rules: stop speed hacks, teleporting, fake health and writing to other players |
| `tests/` | Automated tests for the referee and rules (`npm test`) and a two-player browser test |
| `.github/workflows/android.yml` | Builds `BroadsideBay.apk` (install on a phone) and `BroadsideBay.aab` (Google Play) on every change |
| `.github/workflows/firebase.yml` | Tests, then deploys the referee and the rules to Firebase |

## Online play

* **Sign in with Google**: progress (gold, upgrades, ships sunk) is saved online under `saves/<uid>`.
* **Guest**: plays under a chosen captain name; nothing is saved.
* Hits land instantly on screen. The victim's phone reports each hit; the referee checks it
  (shot really fired, in range, from where the ship really was, not too fast, not in a harbour)
  before it counts. Gold for sinking a player only comes from the referee.
  Repeat cheaters collect strikes and are removed from online play after 5.

## Secrets and settings (GitHub → Settings → Secrets and variables → Actions)

| Name | Kind | Used for |
|---|---|---|
| `ANDROID_KEYSTORE_B64` | secret | the app's signing key (base64) |
| `ANDROID_KEYSTORE_PASSWORD` | secret | its password |
| `FIREBASE_SERVICE_ACCOUNT` | secret | deploying the referee and rules |
| `FIREBASE_PROJECT_ID` | variable | the Firebase project id |

`www/firebase-config.js` holds the public Firebase web config, and `android-app/google-services.json`
the Android config. Both are safe to keep in the repository.
