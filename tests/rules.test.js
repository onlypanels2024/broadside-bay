// Offline check of database.rules.json with targaryen (a Realtime Database rules simulator).
const test = require('node:test');
const assert = require('node:assert');
const targaryen = require('targaryen');
const rules = require('../database.rules.json');

const TS = { '.sv': 'timestamp' };
const T0 = 1_700_000_000_000;
const ship = (x, z, extra = {}) => ({ n: 'Gary', x, z, a: 0, v: 5, t: TS, hp: 5, mx: 5, rs: 0, al: 1, c: 2, ...extra });
const empty = () => targaryen.database(rules, {}, T0).as({ uid: 'A' });

function writeAs(db, uid, path, value, now) {
  const r = db.as({ uid }).write(path, value, { now });
  return r;
}

test('signed-out people cannot read or write anything', () => {
  const db = targaryen.database(rules, {}, T0).as(null);
  assert.strictEqual(db.read('/players').allowed, false);
  assert.strictEqual(db.write('/players/A', ship(21, 0)).allowed, false);
});

test('a new ship must start at a port', () => {
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0), T0).allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(100, 100), T0).allowed, false);
});

test('you can only write your own ship', () => {
  assert.strictEqual(writeAs(empty(), 'A', '/players/B', ship(21, 0), T0).allowed, false);
});

test('normal sailing is allowed, teleporting is not', () => {
  const r1 = writeAs(empty(), 'A', '/players/A', ship(21, 0), T0);
  const db = r1.newDatabase;
  // 0.1 s later moved 2 units: fine
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(23, 0), T0 + 100).allowed, true);
  // 0.1 s later moved 60 units: speed hack
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(81, 0), T0 + 100).allowed, false);
  // after 3 s, 60 units is possible at full speed with boosts? 34*3+6 = 108 -> allowed
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(81, 0), T0 + 3000).allowed, true);
});

test('respawning may jump only to a port', () => {
  const db = writeAs(empty(), 'A', '/players/A', ship(21, 0), T0).newDatabase;
  const far = writeAs(db, 'A', '/players/A', ship(60, 0), T0 + 2000).newDatabase;
  assert.strictEqual(writeAs(far, 'A', '/players/A', ship(196, -160, { rs: 1 }), T0 + 2100).allowed, true);
  assert.strictEqual(writeAs(far, 'A', '/players/A', ship(250, 250, { rs: 1 }), T0 + 2100).allowed, false);
  assert.strictEqual(writeAs(far, 'A', '/players/A', ship(196, -160, { rs: 5 }), T0 + 2100).allowed, false);
});

test('the server clock must be used, and health cannot exceed the hull', () => {
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { t: 123 }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { hp: 9 }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { mx: 20, hp: 20 }), T0).allowed, false);
});

test('names must be 2 to 16 characters and unknown fields are refused', () => {
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { n: 'X' }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { gold: 99999 }), T0).allowed, false);
});

test('cannon shots in the ship record are accepted', () => {
  const s = [[1, 21, 0, 30, 0, T0], [2, 21, 0, 30, 0, T0 + 50]];
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { s }), T0).allowed, true);
});

test('banned players cannot sail', () => {
  const db = targaryen.database(rules, { banned: { A: true } }, T0);
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(21, 0), T0).allowed, false);
});

test('only the victim can report being hit or sunk, and only once', () => {
  const hit = { v: 'B', s: 'A', sid: 3, x: 50, z: 50, t: TS };
  assert.strictEqual(writeAs(empty(), 'B', '/hits/h1', hit, T0).allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/hits/h1', hit, T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'B', '/deaths/d1', { v: 'B', t: TS }, T0).allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/deaths/d1', { v: 'B', t: TS }, T0).allowed, false);
});

test('nobody can give themselves rewards, stats or unban themselves', () => {
  assert.strictEqual(writeAs(empty(), 'A', '/rewards/A/r1', { g: 1000 }, T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/stats/A/kills', 99, T0).allowed, false);
  const banned = targaryen.database(rules, { banned: { A: true } }, T0);
  assert.strictEqual(writeAs(banned, 'A', '/banned/A', null, T0).allowed, false);
  // but you may collect (delete) your own reward
  const withReward = targaryen.database(rules, { rewards: { A: { r1: { g: 150, n: 'x', t: 1 } } } }, T0);
  assert.strictEqual(writeAs(withReward, 'A', '/rewards/A/r1', null, T0).allowed, true);
  assert.strictEqual(writeAs(withReward, 'B', '/rewards/A/r1', null, T0).allowed, false);
});

test('everyone signed in can see who is online', () => {
  assert.strictEqual(empty().as({ uid: 'Z' }).read('/players').allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/online/A', true, T0).allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/online/B', true, T0).allowed, false);
});



test('a hit report may carry the impact time, but not a silly one', () => {
  const ok = { v: 'B', s: 'A', sid: 3, x: 50, z: 50, t: TS, ti: T0 - 800 };
  assert.strictEqual(writeAs(empty(), 'B', '/hits/h1', ok, T0).allowed, true);
  assert.strictEqual(writeAs(empty(), 'B', '/hits/h1', { ...ok, ti: T0 - 60000 }, T0).allowed, false);
});





const save = (ships, hull) => ({ saves: { A: { gold: 100, xp: 0, sunk: 0, earned: 0, up: { hull, sails: 0, reload: 0, triple: 0, broadside: 0 }, ships, ship: 'brig' } } });

test('nobody can write their own save any more: only the referee can', () => {
  const google = { uid: 'A', token: { firebase: { sign_in_provider: 'google.com' } } };
  const db = targaryen.database(rules, {}, T0);
  assert.strictEqual(db.as(google).write('/saves/A', { gold: 999999, earned: 0, sunk: 0, up: {} }, { now: T0 }).allowed, false);
  assert.strictEqual(db.as(google).write('/saves/A/gold', 999999, { now: T0 }).allowed, false);
  assert.strictEqual(db.as(google).read('/saves/A').allowed, true);
  assert.strictEqual(db.as({ uid: 'B' }).read('/saves/A').allowed, false);
});

test('captains can post requests to the referee, but only well-formed ones and only for themselves', () => {
  const ok = (uid, path, v) => writeAs(empty(), uid, path, v, T0).allowed;
  assert.strictEqual(ok('A', '/requests/A/r1', { k: 'kill', e: 'sloop', t: TS }), true);
  assert.strictEqual(ok('A', '/requests/A/r2', { k: 'up', id: 'reload', t: TS }), true);
  assert.strictEqual(ok('A', '/requests/A/r3', { k: 'ship', id: 'manowar', t: TS }), true);
  assert.strictEqual(ok('A', '/requests/B/r1', { k: 'kill', e: 'sloop', t: TS }), false);
  assert.strictEqual(ok('A', '/requests/A/r4', { k: 'gimme', t: TS }), false);
  assert.strictEqual(ok('A', '/requests/A/r5', { k: 'kill', e: 'sloop', t: TS, gold: 5000 }), false);
  assert.strictEqual(ok('A', '/requests/A/r6', { k: 'kill', e: 'leviathan', t: TS }), false);
});

test('you can only sail a ship the referee has recorded you owning', () => {
  const owns = targaryen.database(rules, save({ brig: true, frigate: true }, 0), T0);
  assert.strictEqual(writeAs(owns, 'A', '/players/A', ship(21, 0, { sh: 2, mx: 9, hp: 9 }), T0).allowed, true);
  assert.strictEqual(writeAs(owns, 'A', '/players/A', ship(21, 0, { sh: 4, mx: 15, hp: 15 }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { sh: 1, mx: 7, hp: 7 }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { sh: 0, mx: 5, hp: 5 }), T0).allowed, true);
});

test('your hull can only include armour the referee has recorded you buying', () => {
  const armoured = targaryen.database(rules, save({ brig: true, frigate: true }, 2), T0);
  assert.strictEqual(writeAs(armoured, 'A', '/players/A', ship(21, 0, { sh: 2, mx: 11, hp: 11 }), T0).allowed, true);
  assert.strictEqual(writeAs(armoured, 'A', '/players/A', ship(21, 0, { sh: 2, mx: 12, hp: 12 }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { sh: 0, mx: 6, hp: 6 }), T0).allowed, false);
  // old app versions (no ship class) are held to a plain Brig
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { mx: 8, hp: 8 }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { mx: 5, hp: 5 }), T0).allowed, true);
});

test('your colours at sea must be the ones the referee recorded for you', () => {
  const DW = 'f'.repeat(64);
  const painted = targaryen.database(rules, { saves: { A: { xp: 800, ships: { brig: true }, paint: { lk: '0451300', dw: '' } }, B: { xp: 800, ships: { brig: true }, paint: { lk: '000100z', dw: DW } } } }, T0);
  assert.strictEqual(writeAs(painted, 'A', '/players/A', ship(21, 0, { lk: '0451300' }), T0).allowed, true);
  assert.strictEqual(writeAs(painted, 'A', '/players/A', ship(21, 0, { lk: 'bbbbbbb' }), T0).allowed, false, 'colours never unlocked');
  assert.strictEqual(writeAs(painted, 'B', '/players/B', ship(21, 0, { lk: '000100z', dw: DW }), T0).allowed, true);
  assert.strictEqual(writeAs(painted, 'B', '/players/B', ship(21, 0, { lk: '000100z', dw: '0'.repeat(64) }), T0).allowed, false, 'a drawing the referee never saw');
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { lk: '0001001' }), T0).allowed, false, 'no colours on record yet');
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0), T0).allowed, true, 'older app versions send no colours');
});

test('paint requests must be well formed', () => {
  const ok = (v) => writeAs(empty(), 'A', '/requests/A/r1', v, T0).allowed;
  assert.strictEqual(ok({ k: 'look', lk: '0001001', dw: '', t: TS }), true);
  assert.strictEqual(ok({ k: 'look', lk: '000100z', dw: 'a'.repeat(64), t: TS }), true);
  assert.strictEqual(ok({ k: 'look', lk: 'NOPE', t: TS }), false);
  assert.strictEqual(ok({ k: 'look', lk: '000100z', dw: '<script>', t: TS }), false);
});

test('drawing checks and reports: well formed, only as yourself, never about yourself', () => {
  const ok = (uid, path, v) => writeAs(empty(), uid, path, v, T0).allowed;
  const DW = 'ab'.repeat(32);
  assert.strictEqual(ok('A', '/requests/A/r1', { k: 'check', dw: DW, t: TS }), true);
  assert.strictEqual(ok('A', '/reports/A/r1', { tg: 'B', dw: DW, t: TS }), true);
  assert.strictEqual(ok('A', '/reports/B/r1', { tg: 'C', dw: DW, t: TS }), false, 'as someone else');
  assert.strictEqual(ok('A', '/reports/A/r1', { tg: 'A', dw: DW, t: TS }), false, 'yourself');
  assert.strictEqual(ok('A', '/reports/A/r1', { tg: 'B', dw: 'nope', t: TS }), false);
  assert.strictEqual(ok('A', '/reports/A/r1', { tg: 'B', dw: DW, t: TS, why: 'x' }), false);
  assert.strictEqual(empty().as({ uid: 'A' }).read('/reports/A').allowed, false);
});

test('leaderboards: everyone signed in can read them, nobody can write them', () => {
  const db = targaryen.database(rules, { board: { all: { A: { n: 'Gary', xp: 10 } } } }, T0);
  assert.strictEqual(db.as({ uid: 'B' }).read('/board/all').allowed, true);
  assert.strictEqual(db.as(null).read('/board/all').allowed, false);
  assert.strictEqual(db.as({ uid: 'A' }).write('/board/all/A', { n: 'Gary', xp: 999999 }, { now: T0 }).allowed, false);
  assert.strictEqual(db.as({ uid: 'A' }).write('/board/w1000/A/s', 500, { now: T0 }).allowed, false);
});

test('fleet tag at sea must be your fleet\'s real tag', () => {
  const db = targaryen.database(rules, { saves: { A: { fleet: 'f1', ships: { brig: true } } }, fleets: { f1: { tag: 'WOLF', n: 'Sea Wolves' } } }, T0);
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(21, 0, { fl: 'WOLF' }), T0).allowed, true);
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(21, 0, { fl: 'KING' }), T0).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { fl: 'WOLF' }), T0).allowed, false, 'not in a fleet');
  assert.strictEqual(db.as({ uid: 'A' }).write('/fleets/f1/tag', 'X', { now: T0 }).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/requests/A/r1', { k: 'fleet', op: 'create', n: 'Sea Wolves', tag: 'WOLF', col: 1, em: 2, t: TS }, T0).allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/requests/A/r1', { k: 'fleet', op: 'nuke', t: TS }, T0).allowed, false);
});

test('shared kraken: its health only goes down one hit at a time, and you only count your own hits', () => {
  const db = targaryen.database(rules, { kraken: { 5: { hp: 30, hits: { A: 2 } } } }, T0);
  assert.strictEqual(db.as({ uid: 'A' }).write('/kraken/5/hp', 29, { now: T0 }).allowed, true);
  assert.strictEqual(db.as({ uid: 'A' }).write('/kraken/5/hp', 0, { now: T0 }).allowed, false);
  assert.strictEqual(db.as({ uid: 'A' }).write('/kraken/5/hits/A', 3, { now: T0 }).allowed, true);
  assert.strictEqual(db.as({ uid: 'A' }).write('/kraken/5/hits/A', 30, { now: T0 }).allowed, false);
  assert.strictEqual(db.as({ uid: 'A' }).write('/kraken/5/hits/B', 1, { now: T0 }).allowed, false);
  assert.strictEqual(targaryen.database(rules, {}, T0).as({ uid: 'A' }).write('/kraken/6/hp', 59, { now: T0 }).allowed, true);
});

test('friends: ask anyone, only the asked captain can accept, and nobody can edit someone else\'s list', () => {
  const asA = { uid: 'A' }, asB = { uid: 'B' };
  let db = targaryen.database(rules, {}, T0);
  let r = db.as(asB).write('/friendreq/A/B', { n: 'Maria', t: TS }, { now: T0 }); assert.strictEqual(r.allowed, true); db = r.newDatabase;
  assert.strictEqual(db.as(asB).write('/friendreq/B/B', { n: 'Maria', t: TS }, { now: T0 }).allowed, false, 'not to yourself');
  assert.strictEqual(db.as(asB).write('/friends/A/B', 'Maria', { now: T0 }).allowed, false, 'B cannot add themselves to A');
  r = db.as(asA).write('/friends/A/B', 'Maria', { now: T0 }); assert.strictEqual(r.allowed, true); db = r.newDatabase;
  r = db.as(asA).write('/friends/B/A', 'Gary', { now: T0 }); assert.strictEqual(r.allowed, true, 'A accepts B\'s request'); db = r.newDatabase;
  assert.strictEqual(db.as({ uid: 'C' }).write('/friends/B/C', 'Eve', { now: T0 }).allowed, false, 'no request from B to C');
  assert.strictEqual(db.as(asA).read('/friendreq/A').allowed, true);
  assert.strictEqual(db.as(asB).read('/friendreq/A').allowed, false);
  assert.strictEqual(db.as(asA).write('/friendreq/A/B', null, { now: T0 }).allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { qc: 31 }), T0).allowed, true);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { qc: 'hello rude words' }), T0).allowed, false, 'chat is only numbers');
});

test('duels: a respawn may jump to the duel arena; challenges only as yourself', () => {
  const db = writeAs(empty(), 'A', '/players/A', ship(21, 0), T0).newDatabase;
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(-195 + 20, -200, { rs: 1, du: 'B' }), T0 + 100).allowed, true);
  assert.strictEqual(writeAs(db, 'A', '/players/A', ship(-100, -200, { rs: 1 }), T0 + 100).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(21, 0, { du: 'A' }), T0).allowed, false, 'not yourself');
  let d = targaryen.database(rules, {}, T0);
  let w = d.as({ uid: 'A' }).write('/duelreq/B/A', { n: 'Gary', t: TS }, { now: T0 }); assert.strictEqual(w.allowed, true); d = w.newDatabase;
  assert.strictEqual(d.as({ uid: 'C' }).write('/duelreq/B/A', { n: 'Fake', t: TS }, { now: T0 }).allowed, false);
  assert.strictEqual(d.as({ uid: 'B' }).write('/duelreq/A/B', { n: 'Maria', t: TS, ok: true }, { now: T0 }).allowed, true, 'B accepts by answering in A\'s inbox');
  assert.strictEqual(d.as({ uid: 'C' }).write('/duelreq/A/B', { n: 'Maria', t: TS, ok: true }, { now: T0 }).allowed, false, 'nobody else can accept for B');
  assert.strictEqual(d.as({ uid: 'B' }).write('/duelreq/B/A', null, { now: T0 }).allowed, true, 'B clears its inbox');
});

test('the size of the open sea can only grow during a day, then starts again', () => {
  const day = Math.floor(T0 / 86400000);
  let db = targaryen.database(rules, { world: { day, tier: 1 } }, T0);
  assert.strictEqual(db.as({ uid: 'A' }).write('/world', { day, tier: 2 }, { now: T0 }).allowed, true);
  assert.strictEqual(db.as({ uid: 'A' }).write('/world', { day, tier: 0 }, { now: T0 }).allowed, false, 'no shrinking mid-day');
  assert.strictEqual(db.as({ uid: 'A' }).write('/world', { day: day + 1, tier: 0 }, { now: T0 + 86400000 }).allowed, true, 'new day');
  assert.strictEqual(db.as({ uid: 'A' }).write('/world', { day: day + 9, tier: 4 }, { now: T0 }).allowed, false, 'not a future day');
  assert.strictEqual(db.as({ uid: 'A' }).write('/world', { day, tier: 9 }, { now: T0 }).allowed, false);
  assert.strictEqual(writeAs(empty(), 'A', '/players/A', ship(400, 0, {}), T0).allowed, false, 'new ships still start at a port');
});
