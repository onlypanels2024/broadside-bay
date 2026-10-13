// Run: node --test tests/
const test = require('node:test');
const assert = require('node:assert');
const E = require('../functions/economy.js');

const NOW = 1_800_000_000_000;
const atSea = { x: 80, z: 60, al: 1, t: NOW - 500 };
const seaAt = t => ({ ...atSea, t: t - 300 });
const inPort = { x: 21, z: 0, al: 1, t: NOW - 500, dk: 1 };
const rich = (extra = {}) => ({ ...E.fresh(), gold: 20000, xp: 9500, ...extra });

test('sinking a pirate at sea pays gold, XP and counts the ship', () => {
  const r = E.processRequest(null, { k: 'kill', e: 'sloop' }, atSea, NOW);
  assert.strictEqual(r.ok, true);
  assert.deepStrictEqual([r.save.gold, r.save.xp, r.save.sunk, r.save.earned], [70, 20, 1, 70]);
});

test('kill claims from a harbour, a missing or a sunk ship are refused', () => {
  assert.strictEqual(E.processRequest(null, { k: 'kill', e: 'sloop' }, inPort, NOW).ok, false);
  assert.strictEqual(E.processRequest(null, { k: 'kill', e: 'sloop' }, null, NOW).ok, false);
  assert.strictEqual(E.processRequest(null, { k: 'kill', e: 'sloop' }, { ...atSea, al: 0 }, NOW).ok, false);
  assert.strictEqual(E.processRequest(null, { k: 'kill', e: 'sloop' }, { ...atSea, t: NOW - 60000 }, NOW).ok, false);
});

test('a burst of kills is fine, but claiming faster than pirates appear is not', () => {
  let s = null, ok = 0;
  for (let i = 0; i < 20; i++) { const r = E.processRequest(s, { k: 'kill', e: 'sloop' }, atSea, NOW + i * 200); s = r.save; if (r.ok) ok++; }
  assert.strictEqual(ok, 12, 'the first 12 quick kills count, the rest are refused');
  // a minute later the bucket has refilled 8 kills' worth
  let later = 0;
  for (let i = 0; i < 10; i++) { const r = E.processRequest(s, { k: 'kill', e: 'sloop' }, seaAt(NOW + 64000 + i * 100), NOW + 64000 + i * 100); s = r.save; if (r.ok) later++; }
  assert.ok(later >= 8 && later <= 9, 'refilled about 8 kills, got ' + later);
});

test('spamming fake kills earns a strike', () => {
  let s = null, strikes = 0;
  for (let i = 0; i < 40; i++) { const r = E.processRequest(s, { k: 'kill', e: 'galleon' }, atSea, NOW + i * 10); s = r.save; if (r.strike) strikes++; }
  assert.ok(strikes >= 1);
});

test('bosses can only be claimed one per two minutes', () => {
  let r = E.processRequest(null, { k: 'kill', e: 'boss' }, atSea, NOW);
  assert.strictEqual(r.ok, true); assert.strictEqual(r.save.gold, 550);
  r = E.processRequest(r.save, { k: 'kill', e: 'boss' }, seaAt(NOW + 30000), NOW + 30000);
  assert.strictEqual(r.ok, false);
  r = E.processRequest(r.save, { k: 'kill', e: 'boss' }, seaAt(NOW + 125000), NOW + 125000);
  assert.strictEqual(r.ok, true);
});

test('upgrades: only in harbour, only if affordable, never past the maximum', () => {
  assert.strictEqual(E.processRequest(rich(), { k: 'up', id: 'reload' }, atSea, NOW).ok, false);
  assert.strictEqual(E.processRequest({ ...E.fresh(), gold: 100 }, { k: 'up', id: 'reload' }, inPort, NOW).ok, false);
  let s = rich();
  for (let i = 0; i < 3; i++) { const r = E.processRequest(s, { k: 'up', id: 'reload' }, inPort, NOW); assert.strictEqual(r.ok, true); s = r.save; }
  assert.strictEqual(s.up.reload, 3);
  assert.strictEqual(s.gold, 20000 - 140 - 250 - 360);
  assert.strictEqual(E.processRequest(s, { k: 'up', id: 'reload' }, inPort, NOW).ok, false);
  assert.strictEqual(E.processRequest(s, { k: 'up', id: 'godmode' }, inPort, NOW).ok, false);
});

test('ships: need the rank and the gold, bought in harbour, switch only to owned ships', () => {
  const low = { ...E.fresh(), gold: 20000, xp: 100 };
  assert.strictEqual(E.processRequest(low, { k: 'ship', id: 'corvette' }, inPort, NOW).reason, 'rank too low');
  const poor = { ...E.fresh(), gold: 100, xp: 9999 };
  assert.strictEqual(E.processRequest(poor, { k: 'ship', id: 'frigate' }, inPort, NOW).reason, 'not enough gold');
  assert.strictEqual(E.processRequest(rich(), { k: 'ship', id: 'manowar' }, atSea, NOW).reason, 'not in harbour');
  const r = E.processRequest(rich(), { k: 'ship', id: 'manowar' }, inPort, NOW);
  assert.strictEqual(r.ok, true); assert.strictEqual(r.save.ship, 'manowar'); assert.strictEqual(r.save.gold, 11000);
  const back = E.processRequest(r.save, { k: 'ship', id: 'brig' }, inPort, NOW);
  assert.strictEqual(back.ok, true); assert.strictEqual(back.save.gold, 11000);
});

test('tampered saves are cleaned up: unknown ships, impossible upgrades, negative gold', () => {
  const s = E.norm({ gold: -50, xp: 'lots', up: { hull: 99, reload: 2 }, ships: { yacht: true, frigate: true }, ship: 'yacht' });
  assert.deepStrictEqual([s.gold, s.xp, s.up.hull, s.up.reload, s.ships.yacht, s.ships.frigate, s.ship], [0, 0, 3, 2, undefined, true, 'brig']);
});

test('sinking costs half the gold in the hold; sinking a captain pays 150 gold and 120 XP', () => {
  assert.strictEqual(E.applyDeath({ ...E.fresh(), gold: 301 }).gold, 151);
  const k = E.applyPvpKill(E.fresh());
  assert.deepStrictEqual([k.gold, k.xp, k.sunk], [150, 120, 1]);
});

test('a reset starts a fresh voyage but keeps the kill-rate limiter', () => {
  let s = null;
  for (let i = 0; i < 12; i++) s = E.processRequest(s, { k: 'kill', e: 'sloop' }, atSea, NOW).save;
  const r = E.processRequest(s, { k: 'reset' }, null, NOW);
  assert.strictEqual(r.save.gold, 0);
  assert.strictEqual(E.processRequest(r.save, { k: 'kill', e: 'sloop' }, atSea, NOW).ok, false);
});

test('paint: starter colours for everyone, the rest by rank, drawings from Bosun', () => {
  const DW = '0f'.repeat(32);
  let r = E.processRequest(null, { k: 'look', lk: '1213001' }, null, NOW);
  assert.strictEqual(r.ok, true); assert.deepStrictEqual(r.save.paint, { lk: '1213001' });
  // gilded hull (index b = 11) needs Admiral
  assert.strictEqual(E.processRequest(null, { k: 'look', lk: 'b000001' }, null, NOW).ok, false);
  assert.strictEqual(E.processRequest({ ...E.fresh(), xp: 9000 }, { k: 'look', lk: 'b000001' }, null, NOW).ok, true);
  // own drawing needs rank 2 and a valid drawing
  assert.strictEqual(E.processRequest(null, { k: 'look', lk: '000100z', dw: DW }, null, NOW).ok, false);
  r = E.processRequest(E.applyCheck({ ...E.fresh(), xp: 300 }, DW, true, '', NOW), { k: 'look', lk: '000100z', dw: DW }, atSea, NOW);
  assert.strictEqual(r.ok, true); assert.strictEqual(r.save.paint.dw, DW);
  assert.strictEqual(E.processRequest({ ...E.fresh(), xp: 300 }, { k: 'look', lk: '000100z', dw: 'xyz' }, null, NOW).ok, false);
  // a drawing is dropped when the emblem isn't the drawing
  assert.deepStrictEqual(E.processRequest(null, { k: 'look', lk: '0001003', dw: DW }, null, NOW).save.paint, { lk: '0001003' });
  // nonsense codes
  for (const lk of ['zzzzzzz', '000100', 42, '0001001x']) assert.strictEqual(E.processRequest(null, { k: 'look', lk }, null, NOW).ok, false);
});

test('a tampered save loses paint it could not have unlocked', () => {
  assert.strictEqual(E.norm({ xp: 0, paint: { lk: 'b000001' } }).paint, undefined);
  assert.deepStrictEqual(E.norm({ xp: 9999, paint: { lk: 'b000001' } }).paint, { lk: 'b000001' });
});

test('switching to a ship you own works from the main menu, but not out at sea', () => {
  const s = { ...E.fresh(), ships: { brig: true, frigate: true } };
  assert.strictEqual(E.processRequest(s, { k: 'ship', id: 'frigate' }, null, NOW).ok, true);
  assert.strictEqual(E.processRequest(s, { k: 'ship', id: 'frigate' }, inPort, NOW).ok, true);
  assert.strictEqual(E.processRequest(s, { k: 'ship', id: 'frigate' }, atSea, NOW).ok, false);
  // buying still needs the harbour
  assert.strictEqual(E.processRequest(rich(), { k: 'ship', id: 'frigate' }, null, NOW).ok, false);
});

test("the game's paint ranks match the referee's", () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'src-artifact.html'), 'utf8');
  const m = src.match(/const PAINT_RANK=(\{.*?\});/);
  assert.ok(m, 'PAINT_RANK found in the game');
  assert.deepStrictEqual(JSON.parse(m[1]), E.PAINT_RANK);
  // and each palette in the game has exactly one rank per colour
  const pal = src.match(/const PAINT=\{([\s\S]*?)\n\};/)[1];
  for (const k of ['h', 't', 's', 'p', 'c', 'f']) {
    const row = pal.match(new RegExp('\\b' + k + ':\\[(.*?)\\]'))[1].split(',').length;
    assert.strictEqual(row, E.PAINT_RANK[k].length, 'slot ' + k);
  }
  const em = src.match(/const EMBLEMS=\[(.*?)\];/)[1].split(',').length;
  assert.strictEqual(em, E.PAINT_RANK.e.length);
});

const enc = f => { const b = []; for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) b.push(f(x, y) ? 1 : 0); let h = ''; for (let k = 0; k < 64; k++) { let n = 0; for (let j = 0; j < 4; j++) n = n << 1 | b[k * 4 + j]; h += n.toString(16); } return h; };
const swas = (ox, oy, a, mir, th = 1) => (x, y) => { x = Math.floor((x - ox) / th); y = Math.floor((y - oy) / th); if (x < 0 || y < 0 || x > 2 * a || y > 2 * a) return false; if (mir) x = 2 * a - x; const c = a; return x === c || y === c || (y === 0 && x >= c) || (x === 2 * a && y >= c) || (y === 2 * a && x <= c) || (x === 0 && y <= c); };

test('built-in drawing rules catch swastikas of any size or direction, not ordinary shapes', () => {
  for (const a of [[3, 3, 4, 0], [1, 2, 6, 1], [5, 5, 2, 0], [0, 0, 3, 1, 2], [0, 0, 7, 0], [8, 1, 3, 1]]) assert.strictEqual(E.drawRules(enc(swas(...a))).ok, false, JSON.stringify(a));
  const ok = [
    (x, y) => (x === 2 || x === 8 || x === 14 || y === 2 || y === 8 || y === 14) && x >= 2 && x <= 14 && y >= 2 && y <= 14, // window
    (x, y) => (x === 8 && y > 3 && y < 13) || (y === 8 && x > 3 && x < 13), // plus
    (x, y) => Math.hypot(x - 7.5, y - 7.5) < 6 && Math.hypot(x - 7.5, y - 7.5) > 4, // ring
    (x, y) => x === y || x === 15 - y, // X
  ];
  for (const f of ok) assert.strictEqual(E.drawRules(enc(f)).ok, true);
  assert.strictEqual(E.drawRules('0'.repeat(64)).ok, false, 'empty');
});

test("the game's built-in drawing rules are the referee's, word for word", () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'src-artifact.html'), 'utf8');
  const eco = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'economy.js'), 'utf8');
  const grab = t => t.slice(t.indexOf('/*DRAWRULES*/'), t.indexOf('/*ENDDRAWRULES*/'));
  assert.ok(grab(eco).length > 200);
  assert.strictEqual(grab(src), grab(eco));
});

test('a drawing can only go on a ship once the checker approved it', () => {
  const DW = enc((x, y) => x === y);
  let s = { ...E.fresh(), xp: 300 };
  assert.strictEqual(E.processRequest(s, { k: 'look', lk: '000100z', dw: DW }, null, NOW).reason, 'drawing not approved');
  s = E.applyCheck(s, DW, false, 'rude shape', NOW);
  assert.strictEqual(E.processRequest(s, { k: 'look', lk: '000100z', dw: DW }, null, NOW).ok, false);
  assert.deepStrictEqual([s.dchk.ok, s.dchk.why], [false, 'rude shape']);
  s = E.applyCheck(s, DW, true, 'a line', NOW);
  assert.strictEqual(E.processRequest(s, { k: 'look', lk: '000100z', dw: DW }, null, NOW).ok, true);
});

test('only the newest 12 approved drawings are kept, and a removed drawing comes off the ship', () => {
  let s = { ...E.fresh(), xp: 300 };
  for (let i = 0; i < 15; i++) s = E.applyCheck(s, i.toString(16).padStart(64, 'a'), true, '', NOW + i);
  assert.strictEqual(Object.keys(s.dok).length, 12);
  const DW = 'e'.padStart(64, 'a');
  s = E.processRequest(s, { k: 'look', lk: '000100z', dw: DW }, null, NOW).save;
  assert.strictEqual(s.paint.dw, DW);
  s = E.removeDrawing(s, DW);
  assert.deepStrictEqual(s.paint, { lk: '0001001' });
  assert.strictEqual(s.dok[DW], undefined);
});

test('drawing checks are limited per hour (the AI costs money)', () => {
  let s = null, ok = 0;
  for (let i = 0; i < 20; i++) { const q = E.checkQuota(s, NOW + i); s = q.save; if (q.ok) ok++; }
  assert.strictEqual(ok, E.CHECKS.perHour);
  assert.strictEqual(E.checkQuota(s, NOW + 3600001).ok, true);
});

const DAY = 86400000;
test('daily chest: once a day, bigger every day in a row, back to day 1 after a missed day', () => {
  const t0 = Math.floor(NOW / DAY) * DAY + 3600000;
  let s = null; const got = [];
  for (let d = 0; d < 9; d++) { const r = E.processRequest(s, { k: 'daily' }, null, t0 + d * DAY); assert.strictEqual(r.ok, true); got.push(r.g); s = r.save;
    assert.strictEqual(E.processRequest(s, { k: 'daily' }, null, t0 + d * DAY + 5000).ok, false, 'twice the same day'); }
  assert.deepStrictEqual(got, [100, 150, 200, 300, 400, 500, 750, 750, 750]);
  const r = E.processRequest(s, { k: 'daily' }, null, t0 + 10 * DAY);
  assert.strictEqual(r.g, 100, 'missed a day: streak starts again');
});

test('quests: progress comes from what the referee approved, rewards only once and only when finished', () => {
  // find a day whose quests include sinking sloops
  let day = Math.floor(NOW / DAY); while (!E.questsFor(day).some(q => E.QUESTS[q].id === 'sloops')) day++;
  const t = day * DAY + 1000, i = E.questsFor(day).findIndex(q => E.QUESTS[q].id === 'sloops'), Q = E.QUESTS[E.questsFor(day)[i]];
  let s = null;
  assert.strictEqual(E.processRequest(s, { k: 'quest', id: String(i) }, null, t).reason, 'quest not finished');
  for (let k = 0; k < Q.n; k++) s = E.processRequest(s, { k: 'kill', e: 'sloop' }, seaAt(t + k * 1000), t + k * 1000).save;
  assert.strictEqual(s.q.p[i], Q.n);
  const g0 = s.gold, r = E.processRequest(s, { k: 'quest', id: String(i) }, null, t + 20000);
  assert.strictEqual(r.ok, true); assert.strictEqual(r.save.gold, g0 + Q.g);
  assert.strictEqual(E.processRequest(r.save, { k: 'quest', id: String(i) }, null, t + 21000).reason, 'already claimed');
  // the next day is a fresh start
  assert.strictEqual(E.processRequest(r.save, { k: 'quest', id: String(i) }, null, t + DAY).ok, false);
  assert.strictEqual(E.processRequest(s, { k: 'quest', id: '7' }, null, t).ok, false);
});

test('sinking a captain counts towards the captain quest', () => {
  let day = Math.floor(NOW / DAY); while (!E.questsFor(day).some(q => E.QUESTS[q].id === 'captain')) day++;
  const i = E.questsFor(day).findIndex(q => E.QUESTS[q].id === 'captain');
  const s = E.applyPvpKill(null, day * DAY + 5);
  assert.strictEqual(s.q.p[i], 1);
});

test("the game's daily quest list is the referee's, word for word", () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'src-artifact.html'), 'utf8');
  const eco = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'economy.js'), 'utf8');
  const grab = t => t.slice(t.indexOf('/*DAILYDEF*/'), t.indexOf('/*ENDDAILYDEF*/'));
  assert.ok(grab(eco).length > 200); assert.strictEqual(grab(src), grab(eco));
});

test('fleets: sensible names and tags only; founding needs Bosun and 500 gold, once', () => {
  assert.deepStrictEqual(E.fleetForm({ n: '  The  Black Tide ', tag: 'tide', col: 2, em: 2 }), { ok: true, n: 'The Black Tide', tag: 'TIDE', col: 2, em: 2 });
  assert.strictEqual(E.fleetForm({ n: 'ab', tag: 'TIDE', col: 2, em: 2 }).ok, false);
  assert.strictEqual(E.fleetForm({ n: 'Good name', tag: 'TOOLONG', col: 2, em: 2 }).ok, false);
  assert.strictEqual(E.fleetForm({ n: 'Good name', tag: 'OK', col: 99, em: 2 }).ok, false);
  assert.strictEqual(E.fleetForm({ n: 'Good name', tag: 'OK', col: 1, em: 0 }).ok, false);
  assert.strictEqual(E.fleetPay({ ...E.fresh(), gold: 900, xp: 100 }).ok, false, 'Deckhand');
  assert.strictEqual(E.fleetPay({ ...E.fresh(), gold: 400, xp: 300 }).ok, false, 'not enough gold');
  const r = E.fleetPay({ ...E.fresh(), gold: 900, xp: 300 }); assert.strictEqual(r.ok, true); assert.strictEqual(r.save.gold, 400);
  assert.strictEqual(E.fleetPay({ ...r.save, fleet: 'abc' }).ok, false, 'already in one');
});

test('sea events pay once per their gap; a kraken only once per appearance', () => {
  let s = null;
  let r = E.processRequest(s, { k: 'kill', e: 'treasure' }, atSea, NOW); assert.strictEqual(r.ok, true); assert.strictEqual(r.save.gold, 400); s = r.save;
  assert.strictEqual(E.processRequest(s, { k: 'kill', e: 'treasure' }, seaAt(NOW + 30000), NOW + 30000).ok, false);
  assert.strictEqual(E.processRequest(s, { k: 'kill', e: 'treasure' }, seaAt(NOW + 61000), NOW + 61000).ok, true);
  r = E.processRequest(s, { k: 'kill', e: 'kraken', id: '777' }, atSea, NOW); assert.strictEqual(r.ok, true); s = r.save;
  assert.strictEqual(E.processRequest(s, { k: 'kill', e: 'kraken', id: '777' }, seaAt(NOW + 900000), NOW + 900000).ok, false, 'same kraken twice');
  assert.strictEqual(E.processRequest(s, { k: 'kill', e: 'kraken', id: '778' }, seaAt(NOW + 900000), NOW + 900000).ok, true);
  assert.strictEqual(E.processRequest(null, { k: 'kill', e: 'merchant' }, inPort, NOW).ok, false, 'not from a harbour');
});
