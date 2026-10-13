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

// ---- leaderboards (written only here, read by every signed-in captain)
// board/w<week>/<uid> = {n: name, s: ships sunk, g: gold earned, c: captains sunk} for this week (Monday to Sunday, UTC)
// board/all/<uid> = {n, xp, s} for Google captains (guests start over each time, so they only appear weekly)
const googleCache = new Map();
async function googleUser(uid) {
  if (googleCache.has(uid)) return googleCache.get(uid);
  let g = null;
  try { const u = await admin.auth().getUser(uid); if (u.providerData.some(p => p.providerId === 'google.com')) g = { name: (u.displayName || '').split(' ')[0] }; } catch (e) {}
  googleCache.set(uid, g); return g;
}
const isGoogle = async uid => !!(await googleUser(uid));
const cleanName = n => String(n || '').replace(/[^\p{L}\p{N} '_-]/gu, '').trim().slice(0, 16) || 'Captain';
async function boardAdd(db, uid, name, add, save) {
  const wk = E.weekOf(Date.now());
  await db.ref(`board/w${wk}/${uid}`).transaction(r => {
    const o = r || { s: 0, g: 0, c: 0 };
    o.n = name ? cleanName(name) : (o.n || 'Captain'); o.s = (o.s | 0) + (add.s | 0); o.g = (o.g | 0) + (add.g | 0); o.c = (o.c | 0) + (add.c | 0); return o;
  });
  if (save && save.fleet && add.s) {
    const f = (await db.ref(`fleets/${save.fleet}`).get()).val();
    if (f) await db.ref(`board/f${wk}/${save.fleet}`).transaction(r => ({ n: f.n, tag: f.tag, s: ((r && r.s) | 0) + add.s }));
  }
  if (save && name && await isGoogle(uid)) await db.ref(`board/all/${uid}`).set({ n: cleanName(name), xp: save.xp | 0, s: save.sunk | 0 });
}

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
  if (typeof hit.s === 'string' && typeof hit.v === 'string') {
    const [fs, fv] = await Promise.all([db.ref(`saves/${hit.s}/fleet`).get(), db.ref(`saves/${hit.v}/fleet`).get()]);
    if (fs.val() && fs.val() === fv.val()) return;   // same fleet: no damage, no kill credit
  }
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
  const kres = await db.ref(`saves/${verdict.killer}`).transaction(s => E.applyPvpKill(s, Date.now()));
  const kname = (await db.ref(`players/${verdict.killer}/n`).get()).val();
  await boardAdd(db, verdict.killer, kname, { s: 1, g: E.PVP.g, c: 1 }, kres.snapshot.val());
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
  if (req.k === 'fleet') { await fleetRequest(db, uid, rid, req); return; }
  if (req.k === 'check') {
    await db.ref(`saves/${uid}`).transaction(save => { const out = E.norm(save); out.last = save && typeof save.last === 'string' && save.last > rid ? save.last : rid; return out; });
    return;
  }
  const player = (await db.ref(`players/${uid}`).get()).val();
  // a kraken reward needs that kraken really sunk (shared health at 0) and this captain to have hit it
  let pre = null;
  if (req.k === 'kill' && req.e === 'kraken') {
    const kr = (await db.ref(`kraken/${req.id}`).get()).val(), sl = Number(req.id);
    const fresh = Number.isFinite(sl) && Math.abs(Date.now() - sl * E.KRAKEN.slot) < 1800000;
    if (!fresh || !kr || kr.hp > 0 || !kr.hits || (kr.hits[uid] | 0) < E.KRAKEN.minHits) pre = 'kraken not earned';
    if (fresh) await db.ref(`kraken/${sl - 3}`).remove();
  }
  let verdict = null;
  const res = await db.ref(`saves/${uid}`).transaction(save => {
    verdict = pre ? { save: E.norm(save), ok: false, reason: pre } : E.processRequest(save, req, player, Date.now());
    const out = verdict.save;
    // tells the phone which of its requests have been dealt with
    out.last = save && typeof save.last === 'string' && save.last > rid ? save.last : rid;
    return out;
  });
  if (verdict && !verdict.ok) logger.info('request refused', { uid, k: req.k, reason: verdict.reason });
  if (verdict && verdict.ok && req.k === 'kill') await boardAdd(db, uid, player && player.n, { s: ['sloop', 'galleon', 'boss', 'merchant', 'kraken'].includes(req.e) ? 1 : 0, g: E.KILL[req.e].g }, res.snapshot.val());
  else if (verdict && verdict.ok && (req.k === 'daily' || req.k === 'quest') && await isGoogle(uid)) await boardAdd(db, uid, player && player.n, {}, res.snapshot.val());
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

// ---- fleets: fleets/<id> = {n, tag, col, em, own, m: {uid: name}, at}; fleettags/<TAG> = id; saves/<uid>/fleet = id
async function fleetRequest(db, uid, rid, req) {
  let msg = { ok: false, why: 'unknown fleet request' };
  try { msg = await fleetDo(db, uid, req); } catch (e) { logger.error('fleet request failed', { uid, err: String(e && e.message || e) }); msg = { ok: false, why: 'something went wrong, try again' }; }
  await db.ref(`saves/${uid}`).transaction(save => {
    const out = E.norm(save); out.fmsg = { ok: !!msg.ok, why: String(msg.why || ''), t: Date.now() };
    out.last = save && typeof save.last === 'string' && save.last > rid ? save.last : rid; return out;
  });
}
async function fleetDo(db, uid, req) {
  const g = await googleUser(uid);
  if (!g) return { ok: false, why: 'sign in with Google to join a fleet' };
  const player = (await db.ref(`players/${uid}/n`).get()).val();
  const name = cleanName(player || g.name);
  const save = E.norm((await db.ref(`saves/${uid}`).get()).val());
  if (req.op === 'create') {
    const f = E.fleetForm(req); if (!f.ok) return f;
    const pre = E.fleetPay(save); if (!pre.ok) return pre;
    for (const t of [f.n, f.tag]) { let ai; try { ai = await D.aiCheckText('fleet name', t); } catch (e) { return { ok: false, why: 'the name checker is offline, try again later' }; }
      if (ai.rude) return { ok: false, why: 'that name is not allowed (' + ai.what + ')' }; }
    const fid = db.ref('fleets').push().key;
    const claim = await db.ref(`fleettags/${f.tag}`).transaction(cur => (cur ? undefined : fid));
    if (!claim.committed) return { ok: false, why: 'the tag ' + f.tag + ' is taken' };
    let paid = false;
    await db.ref(`saves/${uid}`).transaction(sv => { const r = E.fleetPay(sv); paid = r.ok; if (!r.ok) return undefined; r.save.fleet = fid; return r.save; });
    if (!paid) { await db.ref(`fleettags/${f.tag}`).remove(); return { ok: false, why: 'not enough gold' }; }
    await db.ref(`fleets/${fid}`).set({ n: f.n, tag: f.tag, col: f.col, em: f.em, own: uid, m: { [uid]: name }, at: Date.now() });
    return { ok: true, why: 'fleet founded' };
  }
  if (req.op === 'join') {
    if (save.fleet) return { ok: false, why: 'leave your fleet first' };
    const fid = String(req.fid || ''); if (!/^[A-Za-z0-9_-]{1,30}$/.test(fid)) return { ok: false, why: 'unknown fleet' };
    let full = false, gone = false;
    const res = await db.ref(`fleets/${fid}`).transaction(f => { gone = false; full = false; if (!f) { gone = true; return f; } const m = f.m || {}; if (Object.keys(m).length >= E.FLEET.max) { full = true; return undefined; } m[uid] = name; f.m = m; return f; });
    if (gone || !res.snapshot.val()) return { ok: false, why: 'that fleet no longer exists' };
    if (full) return { ok: false, why: 'that fleet is full' };
    await db.ref(`saves/${uid}/fleet`).set(fid);
    return { ok: true, why: 'joined ' + res.snapshot.val().n };
  }
  if (req.op === 'leave') {
    if (!save.fleet) return { ok: true, why: 'not in a fleet' };
    await leaveFleet(db, save.fleet, uid);
    return { ok: true, why: 'left the fleet' };
  }
  if (req.op === 'kick') {
    const who = String(req.who || ''); const f = save.fleet && (await db.ref(`fleets/${save.fleet}`).get()).val();
    if (!f || f.own !== uid) return { ok: false, why: 'only the fleet\'s founder can do that' };
    if (who === uid || !(f.m || {})[who]) return { ok: false, why: 'not in your fleet' };
    await leaveFleet(db, save.fleet, who);
    return { ok: true, why: 'captain removed' };
  }
  return { ok: false, why: 'unknown fleet request' };
}
async function leaveFleet(db, fid, uid) {
  const res = await db.ref(`fleets/${fid}`).transaction(f => {
    if (!f) return f; const m = f.m || {}; delete m[uid];
    if (!Object.keys(m).length) return null;
    f.m = m; if (f.own === uid) f.own = Object.keys(m)[0]; return f;
  });
  await db.ref(`saves/${uid}/fleet`).remove();
  if (!res.snapshot.exists()) {   // last captain left: the fleet and its tag are gone
    const tags = (await db.ref('fleettags').orderByValue().equalTo(fid).get()).val() || {};
    await Promise.all(Object.keys(tags).map(t => db.ref(`fleettags/${t}`).remove()));
  }
}
