// Broadside Bay referee running on Firebase. Every hit and every sinking is checked here
// before it counts. Phones show hits instantly; gold and kills only arrive once approved.
// It is also the only thing that changes online progress (gold, XP, upgrades, ships): phones
// send requests to /requests/<uid>, and the result is written to /saves/<uid>.
// Deployed automatically by .github/workflows/firebase.yml (project overboard-2104).
const { onValueCreated } = require('firebase-functions/v2/database');
const { setGlobalOptions } = require('firebase-functions/v2');
const logger = require('firebase-functions/logger');
const admin = require('firebase-admin');
const R = require('./referee');
const E = require('./economy');

admin.initializeApp();
setGlobalOptions({ region: 'europe-west1', maxInstances: 10, memory: '256MiB' });

async function strike(db, uid, reason) {
  const res = await db.ref(`ref/strikes/${uid}`).transaction(n => (n || 0) + 1);
  const count = res.snapshot.val();
  await db.ref(`ref/log`).push({ uid, reason, at: Date.now() });
  logger.warn('referee strike', { uid, reason, count });
  if (count >= R.LIMITS.strikesToBan) {
    await db.ref(`banned/${uid}`).set(true);
    await db.ref(`players/${uid}`).remove();
    logger.warn('referee removed a player from online play', { uid });
  }
}

exports.refereeHit = onValueCreated('/hits/{id}', async (event) => {
  const db = admin.database();
  const hit = event.data.val();
  await event.data.ref.remove();
  if (!hit) return;
  const [s, v] = await Promise.all([db.ref(`players/${hit.s}`).get(), db.ref(`players/${hit.v}`).get()]);
  const shooter = s.val(), victim = v.val();
  const verdict = R.judgeHit(hit, shooter, victim, Date.now());
  if (!verdict.ok) {
    if (verdict.strike) await strike(db, verdict.strike, verdict.reason);
    return;
  }
  const res = await db.ref(`ref/lives/${hit.v}`).transaction(life => R.addHit(life, hit));
  if (R.isGodMode(res.snapshot.val(), victim)) {
    await strike(db, hit.v, 'kept sailing after a sinking amount of damage');
    await db.ref(`ref/lives/${hit.v}/hits`).set(0);
  }
});

exports.refereeDeath = onValueCreated('/deaths/{id}', async (event) => {
  const db = admin.database();
  const death = event.data.val();
  await event.data.ref.remove();
  if (!death || typeof death.v !== 'string') return;
  const lifeRef = db.ref(`ref/lives/${death.v}`);
  const life = (await lifeRef.get()).val();
  await lifeRef.remove();
  await db.ref(`stats/${death.v}/deaths`).transaction(n => (n || 0) + 1);
  // the captain who sank loses half the gold in their hold
  await db.ref(`saves/${death.v}`).transaction(s => E.applyDeath(s));
  const verdict = R.judgeDeath(death, life, Date.now());
  if (!verdict) return;
  const name = ((await db.ref(`players/${death.v}/n`).get()).val()) || 'a captain';
  await db.ref(`saves/${verdict.killer}`).transaction(s => E.applyPvpKill(s));
  // the reward itself is already in the killer's save; this just tells their phone to show a banner
  await db.ref(`rewards/${verdict.killer}`).push({ g: E.PVP.g, n: String(name).slice(0, 16), t: Date.now() });
  await db.ref(`stats/${verdict.killer}/kills`).transaction(n => (n || 0) + 1);
});

exports.refereeRequest = onValueCreated('/requests/{uid}/{rid}', async (event) => {
  const db = admin.database();
  const { uid, rid } = event.params;
  const req = event.data.val();
  await event.data.ref.remove();
  if (!req) return;
  if ((await db.ref(`banned/${uid}`).get()).val()) return;
  const player = (await db.ref(`players/${uid}`).get()).val();
  let verdict = null;
  await db.ref(`saves/${uid}`).transaction(save => {
    verdict = E.processRequest(save, req, player, Date.now());
    const out = verdict.save;
    // tells the phone which of its requests have been dealt with
    out.last = save && typeof save.last === 'string' && save.last > rid ? save.last : rid;
    return out;
  });
  if (verdict && !verdict.ok) logger.info('request refused', { uid, k: req.k, reason: verdict.reason });
  if (verdict && verdict.strike) await strike(db, uid, 'claims: ' + verdict.reason);
});
