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
