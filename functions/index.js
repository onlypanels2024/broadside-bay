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
const D = require('./drawcheck');

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

// Is this drawing allowed? Built-in rules first, then the AI. Returns {ok, why}.
async function judgeDrawing(db, uid, dw, reported) {
  if ((await db.ref(`ref/baddw/${dw}`).get()).val()) return { ok: false, why: 'this drawing has been removed before' };
  const rules = E.drawRules(dw);
  if (!rules.ok) return { ok: false, why: rules.why };
  try {
    const ai = await D.aiCheck(dw, reported);
    logger.info('drawing checked', { uid, dw, rude: ai.rude, what: ai.what, model: ai.model, reported: !!reported });
    await db.ref('status/checker').set({ ok: true, model: ai.model, at: Date.now() });
    return ai.rude ? { ok: false, why: ai.what || 'not allowed' } : { ok: true, why: ai.what };
  } catch (e) {
    logger.error('drawing checker failed', { uid, err: String(e && e.message || e) });
    await db.ref('status/checker').set({ ok: false, err: String(e && e.message || e).slice(0, 300), at: Date.now() });
    return { ok: false, why: 'checker offline', offline: true };
  }
}

// A captain's own drawing needs approving before it goes on a ship ('check' asks; 'look' with a drawing
// that hasn't been approved yet is checked first). Each captain gets a few checks an hour (the AI costs money).
async function checkFirst(db, uid, rid, dw) {
  const cur = E.norm((await db.ref(`saves/${uid}`).get()).val());
  if (cur.dok && cur.dok[dw]) return;
  let allowed = false;
  await db.ref(`saves/${uid}`).transaction(save => { const q = E.checkQuota(save, Date.now()); allowed = q.ok; return q.save; });
  const verdict = allowed ? await judgeDrawing(db, uid, dw, false) : { ok: false, why: 'too many drawings checked this hour' };
  await db.ref(`saves/${uid}`).transaction(save => E.applyCheck(save, dw, verdict.ok, verdict.why, Date.now()));
}

exports.refereeRequest = onValueCreated({ ref: '/requests/{uid}/{rid}', timeoutSeconds: 60 }, async (event) => {
  const db = admin.database();
  const { uid, rid } = event.params;
  const req = event.data.val();
  await event.data.ref.remove();
  if (!req) return;
  if ((await db.ref(`banned/${uid}`).get()).val()) return;
  const dw = typeof req.dw === 'string' && /^[0-9a-f]{64}$/.test(req.dw) ? req.dw : null;
  if (dw && (req.k === 'check' || (req.k === 'look' && typeof req.lk === 'string' && req.lk[6] === 'z'))) await checkFirst(db, uid, rid, dw);
  if (req.k === 'check') {
    await db.ref(`saves/${uid}`).transaction(save => { const out = E.norm(save); out.last = save && typeof save.last === 'string' && save.last > rid ? save.last : rid; return out; });
    return;
  }
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

// Another captain reported a drawing. The AI looks again (told it was reported); if it agrees, or three
// different captains report the same drawing, it is taken off the ship and can never be used again.
exports.refereeReport = onValueCreated({ ref: '/reports/{uid}/{rid}', timeoutSeconds: 60 }, async (event) => {
  const db = admin.database();
  const { uid } = event.params;
  const rep = event.data.val();
  await event.data.ref.remove();
  if (!rep || typeof rep.tg !== 'string' || !/^[0-9a-f]{64}$/.test(rep.dw || '') || rep.tg === uid) return;
  const dw = rep.dw;
  await db.ref(`ref/reports/${dw}/${uid}`).set(Date.now());
  const count = Object.keys((await db.ref(`ref/reports/${dw}`).get()).val() || {}).length;
  await db.ref('ref/log').push({ uid, reason: 'reported a drawing', target: rep.tg, dw, count, at: Date.now() });
  if ((await db.ref(`ref/baddw/${dw}`).get()).val()) return;
  let remove = count >= 3, why = remove ? 'reported by ' + count + ' captains' : '';
  if (!remove && count === 1) {   // one AI look per drawing is enough; more reports then count towards 3
    const v = await judgeDrawing(db, rep.tg, dw, true);
    if (!v.ok && !v.offline) { remove = true; why = v.why; }
  }
  if (!remove) return;
  await db.ref(`ref/baddw/${dw}`).set({ at: Date.now(), why, by: rep.tg });
  await db.ref(`saves/${rep.tg}`).transaction(s => (s ? E.removeDrawing(s, dw) : s));
  logger.warn('drawing removed', { target: rep.tg, dw, why });
  await strike(db, rep.tg, 'rude drawing: ' + why);
});
