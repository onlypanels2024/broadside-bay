// Run: node --test tests/
const test = require('node:test');
const assert = require('node:assert');
const R = require('../functions/referee.js');

const T = 1_000_000;
// shooter at (60,40) fired north (vz -30) at time T
const shooter = (extra = {}) => ({ x: 60, z: 40, t: T + 300, al: 1, s: [[7, 60, 37, 0, -30, T]], ...extra });
const victim = (extra = {}) => ({ x: 60, z: 25, t: T + 500, al: 1, mx: 5, hp: 4, ...extra });
// ball after 0.4s: (60, 37-12=25)
const hit = (extra = {}) => ({ v: 'B', s: 'A', sid: 7, x: 60, z: 25, t: T + 400, ...extra });

test('a real hit is accepted', () => {
  assert.deepStrictEqual(R.judgeHit(hit(), shooter(), victim(), T + 600), { ok: true });
});
test('a hit from a shot that never existed is refused but not punished (could be lag)', () => {
  const r = R.judgeHit(hit({ sid: 99 }), shooter(), victim(), T + 600);
  assert.strictEqual(r.ok, false); assert.strictEqual(r.strike, null);
});
test('a super-fast cannonball is refused and the shooter gets a strike', () => {
  const r = R.judgeHit(hit(), shooter({ s: [[7, 60, 37, 0, -90, T]] }), victim(), T + 600);
  assert.strictEqual(r.ok, false); assert.strictEqual(r.strike, 'A');
});
test('a shot fired from far away from the shooter is refused with a strike', () => {
  const r = R.judgeHit(hit(), shooter({ x: 200, z: 200 }), victim(), T + 600);
  assert.strictEqual(r.ok, false); assert.strictEqual(r.strike, 'A');
});
test('impossible fire rate gets a strike', () => {
  const s = Array.from({ length: 10 }, (_, i) => [i + 1, 60, 37, 0, -30, T + i]);
  s[6] = [7, 60, 37, 0, -30, T];
  const r = R.judgeHit(hit(), shooter({ s }), victim(), T + 600);
  assert.strictEqual(r.ok, false); assert.strictEqual(r.strike, 'A');
});
test('the ball must actually reach the victim', () => {
  const r = R.judgeHit(hit({ x: 90, z: 25 }), shooter(), victim({ x: 90 }), T + 600);
  assert.strictEqual(r.ok, false); assert.strictEqual(r.strike, null);
});
test('no hits count inside a harbour', () => {
  const r = R.judgeHit(hit({ x: 5, z: 5 }), shooter(), victim(), T + 600);
  assert.strictEqual(r.ok, false); assert.match(r.reason, /harbour/);
});
test('you cannot hit yourself', () => {
  assert.strictEqual(R.judgeHit(hit({ s: 'B' }), shooter(), victim(), T + 600).ok, false);
});
test('kill goes to the last valid hitter, not to whoever is claimed', () => {
  let life = R.addHit(null, hit()); life = R.addHit(life, hit({ s: 'C', t: T + 900 }));
  assert.deepStrictEqual(R.judgeDeath({ v: 'B', t: T + 1200 }, life, T + 1300), { killer: 'C', reward: 150 });
});
test('no kill credit if the last hit was long ago', () => {
  const life = R.addHit(null, hit());
  assert.strictEqual(R.judgeDeath({ v: 'B', t: T + 20000 }, life, T + 20000), null);
});
test('a ship that takes far too many hits without sinking is caught', () => {
  let life = null; for (let i = 0; i < 9; i++) life = R.addHit(life, hit());
  assert.strictEqual(R.isGodMode(life, victim()), true);
  let few = null; for (let i = 0; i < 4; i++) few = R.addHit(few, hit());
  assert.strictEqual(R.isGodMode(few, victim()), false);
});

test('a late report still counts when it says when the ball struck', () => {
  // report arrives 1.4 s after firing (lag), impact was at 0.4 s
  const late = hit({ t: T + 1400, ti: T + 400 });
  assert.deepStrictEqual(R.judgeHit(late, shooter(), victim(), T + 1500), { ok: true });
  // a made-up impact time far from the report time is ignored
  const fake = hit({ t: T + 9000, ti: T + 400 });
  assert.strictEqual(R.judgeHit(fake, shooter(), victim(), T + 9100).ok, false);
});
