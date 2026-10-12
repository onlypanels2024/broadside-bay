// Broadside Bay referee: pure checking logic, no Firebase calls, so it can be unit-tested.
// Units: world units (a ship is ~6 long), seconds for speeds, milliseconds for timestamps.

const PORTS = [[0, 0], [175, -160], [-165, 175]];
const SAFE_R = 30;          // harbour safe zone radius
const LIMITS = {
  maxShotSpeed: 52,         // legit max: 30 + half of a boosted ship's speed (~15)
  maxShotAge: 1.6,          // a cannonball flies for 1.1 s; allow lag on top
  hitTolerance: 9,          // how far the ball may be from the reported hit spot
  maxShipSpeed: 34,         // legit max ~30 (bigger sails x3 + speed power-up)
  originSlack: 10,          // shot must start near where the shooter was
  burstWindow: 0.12,        // 10 shots inside this window is impossible
  killWindowMs: 6000,       // the last valid hit within this time gets the kill
  godModeExtraHits: 3,      // hits beyond max hull without sinking = ignoring damage
  strikesToBan: 5,
  reward: 150,
};

const dist = (ax, az, bx, bz) => Math.hypot(ax - bx, az - bz);
const num = v => typeof v === 'number' && Number.isFinite(v);
const inHarbour = (x, z) => PORTS.some(([px, pz]) => dist(x, z, px, pz) < SAFE_R);

// A hit claim is written by the VICTIM's phone when a remote cannonball touches it.
// hit = {v: victimUid, s: shooterUid, sid: shotId, x, z: victim position at impact, t: server time}
// shooter / victim = their current /players node (may be null if they left).
// Returns {ok:true} or {ok:false, reason, strike: uid-or-null}
function judgeHit(hit, shooter, victim, now) {
  if (!hit || typeof hit.s !== 'string' || typeof hit.v !== 'string') return { ok: false, reason: 'malformed', strike: null };
  if (hit.s === hit.v) return { ok: false, reason: 'self hit', strike: null };
  if (!num(hit.x) || !num(hit.z) || !num(hit.t) || !num(hit.sid)) return { ok: false, reason: 'malformed', strike: null };
  if (!shooter) return { ok: false, reason: 'shooter left', strike: null };
  if (inHarbour(hit.x, hit.z)) return { ok: false, reason: 'victim in harbour', strike: null };

  const shots = Array.isArray(shooter.s) ? shooter.s : Object.values(shooter.s || {});
  // Rapid-fire cheat: 10 recorded shots inside an impossible window.
  const times = shots.map(s => s && s[5]).filter(num).sort((a, b) => a - b);
  if (times.length >= 10 && (times[times.length - 1] - times[0]) / 1000 < LIMITS.burstWindow)
    return { ok: false, reason: 'impossible fire rate', strike: hit.s };

  const shot = shots.find(s => Array.isArray(s) && s[0] === hit.sid);
  if (!shot) return { ok: false, reason: 'shot no longer listed', strike: null }; // normal under heavy fire / lag
  const [, x, z, vx, vz, st] = shot;
  if (![x, z, vx, vz, st].every(num)) return { ok: false, reason: 'malformed shot', strike: hit.s };

  if (Math.hypot(vx, vz) > LIMITS.maxShotSpeed) return { ok: false, reason: 'shot too fast', strike: hit.s };

  // The shot must have started near where the shooter's ship actually was.
  if (num(shooter.x) && num(shooter.t)) {
    const since = Math.max(0, (shooter.t - st) / 1000);
    if (dist(x, z, shooter.x, shooter.z) > LIMITS.maxShipSpeed * since + LIMITS.originSlack)
      return { ok: false, reason: 'shot fired from somewhere the ship was not', strike: hit.s };
  }

  // impact time (ti) is when the ball reached the ship; t is when the report arrived
  const ti = num(hit.ti) && hit.ti <= hit.t + 500 && hit.ti >= hit.t - 3000 ? hit.ti : hit.t;
  const age = (ti - st) / 1000;
  if (age < -0.3 || age > LIMITS.maxShotAge) return { ok: false, reason: 'shot too old', strike: null };

  // Where the ball should be at impact time, versus where the victim says it was hit.
  const bx = x + vx * age, bz = z + vz * age;
  if (dist(bx, bz, hit.x, hit.z) > LIMITS.hitTolerance) return { ok: false, reason: 'ball was not there', strike: null };

  // The victim's own reported position must agree with the impact spot.
  if (victim && num(victim.x) && num(victim.t)) {
    const since = Math.abs(victim.t - ti) / 1000;
    if (dist(victim.x, victim.z, hit.x, hit.z) > LIMITS.maxShipSpeed * since + 12)
      return { ok: false, reason: 'victim was elsewhere', strike: null };
  }
  return { ok: true };
}

// life = the referee's running record of valid hits on this victim since they last sank.
function addHit(life, hit) {
  const l = life ? { ...life } : { hits: 0 };
  l.hits = (l.hits || 0) + 1; l.by = hit.s; l.at = hit.t;
  return l;
}

// Ignoring damage: far more valid hits than the hull can take, and still afloat.
function isGodMode(life, victim) {
  if (!life || !victim) return false;
  const mx = num(victim.mx) ? victim.mx : 5;
  return victim.al === 1 && life.hits > mx + LIMITS.godModeExtraHits;
}

// Who gets the kill when a ship reports it sank. Never the claimed killer: the last VALID hit.
function judgeDeath(death, life, now) {
  if (!death || typeof death.v !== 'string') return null;
  if (!life || typeof life.by !== 'string' || !num(life.at)) return null;
  if ((death.t || now) - life.at > LIMITS.killWindowMs) return null;
  if (life.by === death.v) return null;
  return { killer: life.by, reward: LIMITS.reward };
}

module.exports = { judgeHit, addHit, isGodMode, judgeDeath, inHarbour, LIMITS, PORTS, SAFE_R };
