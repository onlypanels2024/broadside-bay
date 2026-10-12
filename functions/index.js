// Broadside Bay referee running on Firebase. Every hit and every sinking is checked here
// before it counts. Phones show hits instantly; gold and kills only arrive once approved.
const { onValueCreated } = require('firebase-functions/v2/database');
const { setGlobalOptions } = require('firebase-functions/v2');
const logger = require('firebase-functions/logger');
const admin = require('firebase-admin');
const R = require('./referee');

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
  if (!death) return;
  const lifeRef = db.ref(`ref/lives/${death.v}`);
  const life = (await lifeRef.get()).val();
  await lifeRef.remove();
  await db.ref(`stats/${death.v}/deaths`).transaction(n => (n || 0) + 1);
  const verdict = R.judgeDeath(death, life, Date.now());
  if (!verdict) return;
  const name = ((await db.ref(`players/${death.v}/n`).get()).val()) || 'a captain';
  await db.ref(`rewards/${verdict.killer}`).push({ g: verdict.reward, n: String(name).slice(0, 16), t: Date.now() });
  await db.ref(`stats/${verdict.killer}/kills`).transaction(n => (n || 0) + 1);
});
