# Season 3: Season of the Voyagers (spec)

Status: **draft for Gary's approval.** Nothing is built until Gary says approve.
Items marked **[proposed]** are my suggestions and need a yes before building.

## 1. Objective

Season 3 takes Broadside Bay "old school": Pacific voyaging canoes, island weapons and sea monsters from Pacific stories, told respectfully.

- **Dates:** Season 3 runs Monday 4 January to Sunday 14 February 2027 (weeks 13 to 18 of the 6-week season cycle).
- **Replaces:** it replaces the cycle's Kraken Season. Kraken Season moves to Season 4 or later.
- **The kraken:** it keeps roaming as normal.
- **Deadline:** the update must reach Google Play by about **28 December 2026**, so players have it before 4 January.
- **Players:** everyone who plays Broadside Bay, on Android and online.
- **Goal:** something new to buy with gold, a new boss to fight together, and Season Pass items worth buying.

### Decided by Gary
- **Ships:** three canoes, each with its own islands' weapon.
  - **Cook Islands outrigger canoe:** sling stones.
  - **Hawaiian double canoe:** spears.
  - **Fijian-style drua:** bows and arrows.
- **Getting the canoes:** **bought with gold during the season, kept forever** after it ends.
- **Strength:** the suggested numbers (section 2).
- **Te Wheke** (giant octopus, season boss): built in the same style as the kraken, and **rises like the kraken**, shared by everyone online.
- **Other monsters:** Giant Clam, Reef Serpent, Storm Bird.
- **Season Pass:** woven-sail looks, the "Wayfinder" wake and the "Navigator" title.
- **Respect:** pictures are reference only. No made-up tattoos, patterns or symbols, no flags, and no gods or guardian spirits as enemies.
- **Look:** the canoes, warriors and Te Wheke follow the approved mock-ups (voyagers_mockups_v2, pictures 1 to 12).

## 2. What gets built

### 2.1 Canoes (new entries in `SHIPS`)
| Canoe | hull | speed | turn | bow | side | rank | price (gold) |
|---|---|---|---|---|---|---|---|
| Outrigger canoe | 4 | 16.5 | 3.6 | 1 | 2 | 2 **[proposed]** | 700 **[proposed]** |
| Fijian-style drua | 8 | 14.2 | 2.8 | 2 | 3 | 3 **[proposed]** | 1900 **[proposed]** |
| Hawaiian double canoe | 11 | 12.8 | 2.3 | 1 | 4 | 5 **[proposed]** | 4200 **[proposed]** |

For comparison, today's ships:

| Ship | hull | speed | turn | bow | side | rank | price (gold) |
|---|---|---|---|---|---|---|---|
| Schooner | 4 | 15.8 | 3.4 | 1 | 2 | 2 | 600 |
| Frigate | 9 | 12.6 | 2.35 | 2 | 5 | 3 | 2000 |
| War Galleon | 12 | 11.4 | 2.0 | 2 | 6 | 5 | 4500 |

- **When to buy:** in the shop only while Season 3 runs. Once bought, a canoe is kept for good, like any other ship.
- **Server check:** the referee refuses a purchase outside the season window. It accepts owned canoes for ever.
- **Models:** built from code (as in the mock-ups), so they stay light on phones. They get the same wave riding, damage, sinking, ship designer paint (where it fits) and ship upgrades as other ships.
- **Online:** other players see your canoe and its crew.

### 2.2 Island weapons (a new look, same rules)
- **Same as cannons:** a shot works exactly like a cannon shot for damage, range, reload and aim. Only the look and sound change. That keeps fights fair against every other ship.
- **What each fires:**
  - Outrigger: sling stones with a short white trail and a whirr sound.
  - Double canoe: spears, in a flatter, heavier arc.
  - Drua: arrows that twang and stick into the target's hull for a few seconds.
- **Warriors:** each canoe carries its warriors (as in mock-ups 10 to 12). They animate a simple throw, draw or swing when you fire. At game-camera distance a simpler figure is drawn.
- **Shot styles:** Season Pass shot styles still apply. Canoes show them as tinted stones, spears or arrows **[proposed]**.

### 2.3 Te Wheke (season boss)
- **Model:** the kraken's way of building (vertex-coloured skin, kraken texture and bumps, jointed suckered arms, glowing eyes), with the octopus shape from mock-ups 5 and 8.
- **Schedule:** like the kraken, one shared Te Wheke for everyone online: a new one can rise every 8 minutes and stays 4 minutes. It works off its own slots, offset by 4 minutes from the kraken, so they take turns **[proposed]**.
- **Fight:**
  - Red warning rings before an arm slams.
  - Shooting a raised arm stuns it.
  - The final hit goes to whoever lands it.
- **Health and hits:** the same rules as the kraken: shared health, at least 3 hits from you to earn the reward, and the referee checks the kill.
- **Reward:** gold and XP like the kraken. There's also a new achievement, "Kupe's Chase", with the title "Octopus Hunter" **[proposed name]**.

### 2.4 Season monsters (mock-ups to be approved first)
- **Giant Clam:** sits near islands with a pearl inside and only takes damage while open. Pays gold and sometimes a pearl bonus.
- **Reef Serpent:** circles in shallow water and is only hittable when it surfaces.
- **Storm Bird:** appears in storms and swoops down at ships; you hit it while it dives.
- **Size:** these are smaller fights than Te Wheke, more like the shark. Server-checked like the shark.

### 2.5 Season Pass for Season 3 (same price and 10 steps as before)
- **New items:**
  - The Wayfinder wake (needs a trail slot, see Risks).
  - A woven-sail look for every ship.
  - A shot style.
  - The "Navigator" title.
- **Shop:** they appear in `PASS.items[3]` and the shop as usual.
- **Renaming:** `s3cap` ("Kraken Season Captain") is renamed for Voyagers.

### 2.6 Season text and look
- **Season rules:** the `seasonAt` rules: season 3 = Voyagers. The cycle (gold, kraken, ghost, storm) carries on after it, with Kraken Season next.
- **In the game:** season banner, Captain's log entries, release notes and store text.
- **Not changed:** nothing changes for seasons 1 and 2. Christmas and New Year keep working exactly as now.

### 2.7 Optional, needs Gary's go-ahead and setup
- **Meshy models:** Meshy 3D models for Te Wheke and the monsters, only if Meshy can connect and Gary approves the credits. Every model goes through `tools/prepare_model.py`, plus a colour check with and without it on screen.

## 3. Commands

```
python3 build_app.py                       # src-artifact.html -> www/index.html
python3 tests/browser/make_test_page.py    # builds the browser test page
python3 -m http.server 8766                # from the repo root, in the background; stop it when done
npm test                                   # economy, referee and rules tests (node --test)
python3 tests/browser/run_<area>.py        # one browser test, e.g. run_xmas.py, run_shop.py
python3 tools/prepare_model.py IN.glb www/models/NAME.glb   # any new 3D model
```

- Release happens through a push to `main`:
  - `firebase.yml` deploys the database rules, functions and website.
  - `android.yml` builds the app and makes release v1.0.<run number>.
- Gary uploads the AAB to Google Play himself.

## 4. Project structure (where the work goes)

- **`src-artifact.html`:** the game: canoe models, warriors, weapons, Te Wheke, monsters, UI.
- **`functions/economy.js`:** rules shared with the game:
  - the SEASONDEF block (Voyagers) and the ACHDEF block (new achievement), copied word for word between the markers;
  - `SHIPS` prices and the season window;
  - `PASS.items[3]`;
  - Te Wheke and monster rewards.
- **`functions/index.js`:** referee checks for the season window, buying canoes, and Te Wheke and monster kills.
- **`database.rules.json`:** the shared Te Wheke node (like `kraken` and `elf`), and the new kill kinds.
- **`www/js/net-firebase.js`, `build_app.py`:** online watch and hit for Te Wheke (like elfWatch and elfHit).
- **Tests:**
  - `tests/economy.test.js` and `tests/referee.test.js`: the new rules.
  - `tests/browser/run_voyagers.py` (new): uses `__wxShift` to move the clock into Season 3.
- **New-feature work:** done on a `voyagers` branch, and merged to `main` only after Gary approves.

## 5. Code style

- **Follow the file:** compact one-line functions in the existing style, plain JS inside the game's IIFE, and three.js built-in geometry.
- **No new libraries.**
- **Shared rules:** they live in the SEASONDEF and ACHDEF blocks and are copied word for word to both files.
- **Dates:** time windows are in UTC milliseconds, with a comment giving the Malta time.
- **Comments:** short and plain.
- **Scope:** one feature changes nothing else. Existing ships, seasons, Christmas, New Year, ads and the shop must behave exactly as before.

## 6. Testing

- **While building:** run only a quick test of the part just changed (Gary's rule).
- **Once at the end, before anything goes to Gary or Google Play:**
  - `npm test` (all pass);
  - every browser test (`tests/browser/run_*.py`);
  - the new `run_voyagers.py`, which checks:
    - season 3 is Voyagers and Kraken Season is next;
    - canoes are only for sale in season and kept afterwards;
    - the referee refuses buying out of season;
    - weapon shots damage like cannons;
    - Te Wheke rises on its slots, is shared online, pays out once, and is checked by the referee;
    - the Season Pass items unlock;
    - the season rules hold for every date from now to 2028;
  - a before/after screenshot check that nothing outside the new features changed colour or layout;
  - a phone-speed check: with a full lobby of canoes and Te Wheke on screen, the frame rate must not drop below today's;
  - an independent review by the code-review, test, performance and security checkers (Agent Protocols plugin), once.
- **Previews:** screenshots and a short clip go to Gary before release. **Never send an untested or bugged APK.**

## 7. Boundaries

**Always**
- Show Gary pictures first, and build or publish only after he approves (parts can be approved separately).
- Tell Gary everything, including mistakes and fixes behind the scenes.
- Give release notes in the exact paste-ready format, e.g. `<en-GB>…</en-GB>`.
- Use facts only, never assumed numbers.
- Respect Pacific cultures, as written in section 1.
- Stop test servers when done, and say so.

**Ask first**
- Any **[proposed]** item above.
- Spending Meshy credits, or anything else that costs money.
- Changing existing ships, prices or balance.
- Merging to `main` (that deploys straight away).

**Never**
- Change anything outside Season 3 without asking.
- Repeat trial-and-error runs.
- Enter payment details, keys or passwords.
- Post as Gary's personal account.
- Send an APK that hasn't been fully tested.

## 8. Risks and open points

- **Trail slots:** the trail slot digits (0 to 9) are full (8 Candy cane, 9 Abyss). The Wayfinder wake needs the save format to allow more than 10 trails. That's a small change to how cosmetics are stored, and it needs careful testing with existing saves.
- **Phone speed:** many warriors and arrows on screen at once. Plan: a simpler figure at a distance, a cap on how many stuck arrows are shown, and the speed check in section 6.
- **Time:** the work has to be finished, tested and sent to Gary by about 22 December, so he has time to upload by 28 December.
