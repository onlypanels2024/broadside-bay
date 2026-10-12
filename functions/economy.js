// Broadside Bay economy referee: the ONLY thing allowed to change online gold, XP, upgrades and ships.
// Phones send requests ("I sank a sloop", "buy Quick reload"); this decides what actually happens.
// Pure functions, no Firebase calls, so it can be unit-tested (and run in the browser test harness).
(function (root) {
  'use strict';
  const PORTS = [[0, 0], [175, -160], [-165, 175]];
  const SAFE_R = 30;
  const RANK_XP = [0, 250, 700, 1500, 3000, 5500, 9000];           // Deckhand .. Admiral
  const SHIPS = {
    brig: { rank: 1, price: 0, hull: 5 },
    corvette: { rank: 2, price: 800, hull: 7 },
    frigate: { rank: 3, price: 2000, hull: 9 },
    galleon: { rank: 5, price: 4500, hull: 12 },
    manowar: { rank: 7, price: 9000, hull: 15 },
  };
  const SHIP_ORDER = ['brig', 'corvette', 'frigate', 'galleon', 'manowar'];
  const UPGRADES = {
    broadside: { max: 1, price: () => 350 },
    reload: { max: 3, price: l => 140 + l * 110 },
    sails: { max: 3, price: l => 120 + l * 90 },
    hull: { max: 3, price: l => 150 + l * 120 },
    triple: { max: 1, price: () => 250 },
  };
  const REPAIR = 60;
  // Online, coins dropped by a sunk ship are included in the kill reward (pickups are just for show).
  const KILL = {
    sloop: { g: 70, xp: 20, pts: 1 },
    galleon: { g: 210, xp: 50, pts: 2.5 },
    boss: { g: 550, xp: 250, pts: 0 },
  };
  // How fast pirates can realistically be sunk: a bucket of 12 "sloop points" refilled at 8 per minute,
  // and at most one boss every 2 minutes (bosses appear every 4).
  const RATE = { cap: 12, perMin: 8, bossGapMs: 120000, maxRejects: 12, freshMs: 15000 };
  const PVP = { g: 150, xp: 120 };

  const num = v => typeof v === 'number' && Number.isFinite(v);
  const inHarbour = (x, z) => num(x) && num(z) && PORTS.some(([px, pz]) => Math.hypot(x - px, z - pz) < SAFE_R);
  const rankIdx = xp => { let r = 0; RANK_XP.forEach((t, i) => { if (xp >= t) r = i; }); return r; };

  function fresh() {
    return { gold: 0, earned: 0, sunk: 0, xp: 0, up: { hull: 0, sails: 0, reload: 0, triple: 0, broadside: 0 }, ships: { brig: true }, ship: 'brig' };
  }
  function norm(s) {
    const f = fresh();
    if (!s || typeof s !== 'object') return f;
    const o = { ...f, ...s };
    for (const k of ['gold', 'earned', 'sunk', 'xp']) o[k] = num(o[k]) && o[k] >= 0 ? Math.floor(o[k]) : 0;
    o.up = { ...f.up };
    for (const k in f.up) { const v = s.up && s.up[k]; o.up[k] = num(v) ? Math.max(0, Math.min(UPGRADES[k].max, Math.floor(v))) : 0; }
    o.ships = { brig: true };
    if (s.ships && typeof s.ships === 'object') for (const k in s.ships) if (SHIPS[k] && s.ships[k] === true) o.ships[k] = true;
    o.ship = o.ships[s.ship] ? s.ship : 'brig';
    if (s.rl && typeof s.rl === 'object') o.rl = { ...s.rl }; else delete o.rl;
    return o;
  }
  const docked = p => !!p && inHarbour(p.x, p.z);
  const atSea = (p, now) => !!p && p.al === 1 && num(p.t) && now - p.t <= RATE.freshMs && !inHarbour(p.x, p.z);

  // req = {k:'kill'|'up'|'repair'|'ship'|'reset', e?, id?}; player = this captain's /players record (or null)
  // Returns {save, ok, reason, strike}
  function processRequest(saveIn, req, player, now) {
    const s = norm(saveIn);
    const no = (reason, strike) => ({ save: s, ok: false, reason, strike: !!strike });
    if (!req || typeof req.k !== 'string') return no('malformed');
    switch (req.k) {
      case 'kill': {
        const K = KILL[req.e];
        if (!K) return no('unknown ship type');
        if (!atSea(player, now)) return no('not at sea');
        const rl = s.rl ? { ...s.rl } : { b: RATE.cap, t: now, lb: 0, rj: 0 };
        rl.b = Math.min(RATE.cap, (num(rl.b) ? rl.b : RATE.cap) + Math.max(0, now - (num(rl.t) ? rl.t : now)) / 60000 * RATE.perMin);
        rl.t = now;
        const reject = reason => {
          rl.rj = (rl.rj | 0) + 1; const strike = rl.rj >= RATE.maxRejects; if (strike) rl.rj = 0;
          s.rl = rl; return no(reason, strike);
        };
        if (req.e === 'boss') { if (now - (rl.lb || 0) < RATE.bossGapMs) return reject('boss claimed too soon'); rl.lb = now; }
        else { if (rl.b < K.pts) return reject('sinking faster than pirates appear'); rl.b -= K.pts; }
        rl.rj = 0; s.rl = rl;
        s.gold += K.g; s.earned += K.g; s.xp += K.xp; s.sunk += 1;
        return { save: s, ok: true };
      }
      case 'up': {
        const U = UPGRADES[req.id];
        if (!U) return no('unknown upgrade');
        if (!docked(player)) return no('not in harbour');
        const lvl = s.up[req.id];
        if (lvl >= U.max) return no('already fitted');
        const price = U.price(lvl);
        if (s.gold < price) return no('not enough gold');
        s.gold -= price; s.up[req.id] = lvl + 1;
        return { save: s, ok: true };
      }
      case 'repair': {
        if (!docked(player)) return no('not in harbour');
        if (s.gold < REPAIR) return no('not enough gold');
        s.gold -= REPAIR; return { save: s, ok: true };
      }
      case 'ship': {
        const S = SHIPS[req.id];
        if (!S) return no('unknown ship');
        if (!docked(player)) return no('not in harbour');
        if (s.ships[req.id]) { s.ship = req.id; return { save: s, ok: true }; }
        if (rankIdx(s.xp) + 1 < S.rank) return no('rank too low');
        if (s.gold < S.price) return no('not enough gold');
        s.gold -= S.price; s.ships[req.id] = true; s.ship = req.id;
        return { save: s, ok: true };
      }
      case 'reset': {
        const f = fresh(); if (s.rl) f.rl = s.rl;   // keep the rate limiter so a reset can't be used to farm
        return { save: f, ok: true };
      }
      default: return no('unknown request');
    }
  }
  // A captain sank: they lose half the gold in their hold.
  function applyDeath(saveIn) { const s = norm(saveIn); s.gold -= Math.floor(s.gold / 2); return s; }
  // A captain sank another captain (already confirmed by the hit referee).
  function applyPvpKill(saveIn) { const s = norm(saveIn); s.gold += PVP.g; s.earned += PVP.g; s.xp += PVP.xp; s.sunk += 1; return s; }

  const api = { processRequest, applyDeath, applyPvpKill, fresh, norm, rankIdx, inHarbour, SHIPS, SHIP_ORDER, UPGRADES, KILL, RATE, PVP, RANK_XP, REPAIR };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.ECONOMY = api;
})(typeof self !== 'undefined' ? self : this);
